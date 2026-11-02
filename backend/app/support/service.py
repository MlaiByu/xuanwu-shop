"""会话编排：把 LangGraph 的执行过程翻译成 SSE 事件。

事件协议（`data: {json}` 一行一条）：
    meta    会话建立，带模型模式（llm / rule）
    intent  意图识别结果
    tool    工具查询结果摘要
    policy  命中的政策条目
    token   回复分块（前端做打字机）
    handoff 已转人工 + 工单号
    done    结束，带完整回复

会话暂存内存：单机演示足够。生产换成 Redis 或 support_messages 表即可，
接口形状（stream 产出事件）不变。
"""

import time
import uuid
from collections import OrderedDict
from typing import Any, Iterator

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.support.graph import INTENT_LABEL, get_graph
from app.support.llm import get_llm

MAX_HISTORY = 20
MAX_SESSIONS = 500
CHUNK_SIZE = 3
CHUNK_DELAY = 0.012

_SESSIONS: "OrderedDict[str, list[dict[str, str]]]" = OrderedDict()


def _history(session_id: str) -> list[dict[str, str]]:
    if session_id not in _SESSIONS:
        if len(_SESSIONS) >= MAX_SESSIONS:
            _SESSIONS.popitem(last=False)
        _SESSIONS[session_id] = []
    _SESSIONS.move_to_end(session_id)
    return _SESSIONS[session_id]


def reset_sessions() -> None:
    """测试用：清空内存会话。"""
    _SESSIONS.clear()


def _to_messages(history: list[dict[str, str]]) -> list[Any]:
    messages: list[Any] = []
    for item in history[-MAX_HISTORY:]:
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        else:
            messages.append(AIMessage(content=item["content"]))
    return messages


class SupportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.graph = get_graph()
        self.llm = get_llm()

    @property
    def mode(self) -> str:
        return self.llm.mode

    def create_session(self) -> str:
        session_id = uuid.uuid4().hex
        _history(session_id)
        return session_id

    def history(self, session_id: str) -> list[dict[str, str]]:
        return list(_history(session_id))

    def stream(
        self,
        session_id: str,
        text: str,
        user_id: int | None = None,
        nickname: str | None = None,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        history = _history(session_id)
        history.append({"role": "user", "content": text})

        state = {
            "messages": _to_messages(history),
            "session_id": session_id,
            "user_id": user_id,
            "nickname": nickname,
        }
        config = {"configurable": {"db": self.db}}

        yield "meta", {"session_id": session_id, "mode": self.mode}

        final: dict[str, Any] = {}
        for chunk in self.graph.stream(state, config=config, stream_mode="updates"):
            for node, delta in chunk.items():
                if not isinstance(delta, dict):
                    continue
                final.update(delta)

                if node == "classify":
                    intent = delta.get("intent", "chitchat")
                    yield "intent", {
                        "intent": intent,
                        "label": INTENT_LABEL.get(intent, "闲聊"),
                        "confidence": round(float(delta.get("confidence", 0)), 2),
                    }
                elif node in ("query_order", "query_logistics", "search_product"):
                    result = delta.get("tool_result") or {}
                    yield "tool", {
                        "name": delta.get("tool_name"),
                        "ok": bool(result.get("ok")),
                        "summary": _tool_summary(result),
                    }
                elif node == "retrieve_policy":
                    hits = delta.get("policy_hits") or []
                    if hits:
                        yield "policy", {"titles": [item["title"] for item in hits]}

        reply = final.get("reply") or "抱歉，我没理解你的问题，可以换种说法再说一次吗？"
        for piece in _split(reply):
            yield "token", {"text": piece}
            time.sleep(CHUNK_DELAY)

        if final.get("need_human"):
            yield "handoff", {
                "ticket_id": final.get("ticket_id"),
                "reason": final.get("handoff_reason") or "需要人工协助",
            }

        history.append({"role": "assistant", "content": reply})
        if len(history) > MAX_HISTORY:
            del history[: len(history) - MAX_HISTORY]

        yield "done", {
            "reply": reply,
            "intent": final.get("intent", "chitchat"),
            "need_human": bool(final.get("need_human")),
            "ticket_id": final.get("ticket_id"),
            "mode": self.mode,
        }


def _split(text: str, size: int = CHUNK_SIZE) -> Iterator[str]:
    for index in range(0, len(text), size):
        yield text[index : index + size]


def _tool_summary(result: dict[str, Any]) -> str:
    """只给前端一句人类可读的摘要，不透传内部结构。"""
    if not result.get("ok"):
        return result.get("message") or "没有查到结果"
    kind = result.get("type")
    data = result.get("data") or {}
    if kind == "order" and "orders" in data:
        return f"查到 {len(data['orders'])} 笔订单"
    if kind == "order":
        return f"订单 {data.get('order_no')} · {data.get('status_text')}"
    if kind == "logistics":
        return f"{data.get('order_no')} · {data.get('status_text')}"
    if kind == "product":
        return f"匹配 {len(data.get('products') or [])} 件商品"
    return "查询完成"
