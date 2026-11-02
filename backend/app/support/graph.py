"""LangGraph 状态图：分类 → 查事实 → 生成 → 判断转人工。

为什么用图而不是链：客服的真实路径有分支（查单 / 查物流 / 查商品 / 政策）
和回退（查不到 → 转人工），链式编排表达不了条件边。
"""

import difflib
import time
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from app.models.product import Product
from app.support.llm import get_llm
from app.support.policies import search_policies
from app.support.state import SupportState
from app.support.tools import (
    STATUS_TEXT,
    extract_order_no,
    logistics_status,
    order_detail,
    recent_orders,
    search_products,
)

# 顺序即优先级：情绪/投诉 > 订单 > 物流 > 政策 > 商品 > 闲聊
# 说明：「订单」排在「物流」前，避免「我的订单到哪了」被误判成查物流；
# 「政策」排在「商品」前，避免「有没有发票」被商品意图抢走。
INTENT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("human", ["人工", "真人", "投诉", "差评", "举报", "骗子", "曝光", "太坑", "生气", "12315"]),
    ("order", ["订单", "单号", "我买的", "下单", "买的东西"]),
    ("logistics", ["物流", "快递", "到哪", "送到", "签收", "配送", "几天到", "什么时候到"]),
    ("policy", ["退货", "退款", "换货", "运费", "包邮", "发票", "支付", "地址", "取消", "保修", "质量", "退"]),
    ("product", ["有没有", "有吗", "有货", "库存", "多少钱", "价格", "参数", "规格", "推荐", "哪款", "什么价", "卖不卖"]),
]

HANDOFF_TRIGGERS = ["投诉", "差评", "举报", "骗子", "曝光", "12315", "太坑", "气死"]

# 追问信号：短句、指代词、只问某个属性。命中则继承上一轮意图。
FOLLOWUP_HINTS = ["这个", "那个", "它", "这款", "那款", "那单", "这单", "还有", "多少钱", "有货", "什么时候"]

# 礼貌/结束语不算追问，避免「谢谢」被当成上一轮的延续
SMALLTALK = ["你好", "您好", "在吗", "谢谢", "再见", "拜拜", "hi", "hello", "嗯", "好的"]

INTENT_LABEL = {
    "order": "查订单",
    "logistics": "查物流",
    "product": "问商品",
    "policy": "问政策",
    "human": "转人工",
    "chitchat": "闲聊",
}


def _last_user_text(state: SupportState) -> str:
    for message in reversed(state.get("messages") or []):
        if getattr(message, "type", "") in ("human", "user"):
            return message.content if isinstance(message.content, str) else ""
    return ""


def _is_followup(text: str) -> bool:
    """判断是不是在追问上一轮的话题。"""
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    if any(word in normalized for word in SMALLTALK):
        return False
    if len(normalized) <= 12:
        return True
    return any(word in normalized for word in FOLLOWUP_HINTS)


def _classify(text: str, prev_intent: str | None = None) -> tuple[str, float]:
    for intent, keywords in INTENT_KEYWORDS:
        hits = [word for word in keywords if word in text]
        if hits:
            confidence = min(0.6 + 0.1 * len(hits), 0.95)
            return intent, confidence

    # 没有明确意图词时，若上一轮在聊商品/订单且这句像追问，就沿用它
    if prev_intent in ("product", "order", "logistics") and _is_followup(text):
        return prev_intent, 0.5
    return "chitchat", 0.35


def _scan_context(
    state: SupportState, names: list[str] | None = None
) -> tuple[str | None, str | None, str | None]:
    """从历史消息回算会话上下文：上一轮意图、商品关键词、订单号。

    会话只存文本（内存 / Redis 都轻量），因此每轮重新扫描最近 6 条用户消息，
    成本可以忽略，但换来了「那这个呢」「多少钱」这类追问的连续性。

    names 传入在售商品名时，历史里的裸商品名也能被识别成 product，
    否则「卫龙辣条」在历史里会记成闲聊，下一轮追问就断链了。
    """
    texts = [
        message.content
        for message in (state.get("messages") or [])
        if getattr(message, "type", "") in ("human", "user")
        and isinstance(message.content, str)
    ]
    prev_intent: str | None = None
    prev_keyword: str | None = None
    prev_order: str | None = None

    for text in texts[:-1][-6:]:  # 排除当前这条
        # 扫描时也要带上上下文，否则「卫龙辣条」这种追问在历史里会被当成闲聊，
        # 导致下一轮「多少钱」回退到更早的错误关键词。
        intent, _ = _classify(text, prev_intent)
        keyword = _extract_product_keyword(text)

        if intent in ("chitchat", "product") and names:
            matched = _match_product_name(text, names)
            if matched:
                intent, keyword = ("product" if intent == "chitchat" else intent), matched

        if intent == "product":
            prev_intent = "product"
            if keyword:
                prev_keyword = keyword
        elif intent in ("order", "logistics"):
            prev_intent = intent
            order_no = extract_order_no(text)
            if order_no:
                prev_order = order_no
        elif intent in ("policy", "human"):
            prev_intent = intent

    return prev_intent, prev_keyword, prev_order


_NAME_CACHE: dict[str, Any] = {"at": 0.0, "names": []}
_NAME_TTL = 60.0


def _product_names(db) -> list[str]:
    """在售商品名缓存（60 秒），用于把人话里的商品名认出来。"""
    if db is None:
        return list(_NAME_CACHE["names"])
    now = time.time()
    if _NAME_CACHE["names"] and now - float(_NAME_CACHE["at"]) < _NAME_TTL:
        return list(_NAME_CACHE["names"])
    try:
        names = list(db.scalars(select(Product.name).where(Product.is_active.is_(True))))
    except Exception:  # noqa: BLE001 - 查不到就退回缓存，不影响对话
        return list(_NAME_CACHE["names"])
    _NAME_CACHE["at"] = now
    _NAME_CACHE["names"] = names
    return names


def _match_product_name(text: str, names: list[str]) -> str | None:
    """把用户说的商品名对齐到标准商品名。

    先做包含匹配（「卫龙辣条还有多少」包含「卫龙辣条」），
    再做模糊匹配（「威龙辣条」→「卫龙辣条」），容忍少量错别字。
    """
    if not names:
        return None
    cleaned = _extract_product_keyword(text)
    for name in names:
        if name and (name in text or (cleaned and name in cleaned)):
            return name
    if cleaned:
        close = difflib.get_close_matches(cleaned, names, n=1, cutoff=0.62)
        if close:
            return close[0]
    return None


def classify_node(state: SupportState, config: dict[str, Any]) -> dict[str, Any]:
    text = _last_user_text(state)
    names = _product_names(_db_of(config))
    prev_intent, prev_keyword, prev_order = _scan_context(state, names)

    intent, confidence = _classify(text, prev_intent)
    order_no = extract_order_no(text) or prev_order

    keyword = _extract_product_keyword(text)
    if not keyword and intent == "product":
        # 「多少钱」「有货吗」这类没有实体的追问，沿用上一轮的商品
        keyword = prev_keyword or ""

    # 商品实体对齐：用户可能只说商品名（甚至打错字）。
    # 这一步既负责把 chitchat 提升成 product，也负责把错别字纠正成标准名，
    # 否则「威龙辣条」会带着错字去查库，永远查不到。
    if intent in ("chitchat", "product"):
        matched = _match_product_name(text, names)
        if matched:
            keyword = matched
            if intent == "chitchat":
                intent, confidence = "product", 0.65

    return {
        "intent": intent,
        "confidence": confidence,
        "order_no": order_no,
        "prev_intent": prev_intent,
        "prev_product_keyword": prev_keyword,
        "prev_order_no": prev_order,
        "product_keyword": keyword,
    }


def _route_by_intent(state: SupportState) -> str:
    return {
        "order": "query_order",
        "logistics": "query_logistics",
        "product": "search_product",
        "policy": "retrieve_policy",
        "human": "handoff",
    }.get(state.get("intent", ""), "generate")


def _previous_user_text(state: SupportState) -> str:
    texts = [
        message.content
        for message in (state.get("messages") or [])
        if getattr(message, "type", "") in ("human", "user")
        and isinstance(message.content, str)
    ]
    return texts[-2] if len(texts) >= 2 else ""


def retrieve_policy_node(state: SupportState) -> dict[str, Any]:
    text = _last_user_text(state)
    hits = search_policies(text)
    if not hits and state.get("prev_intent") == "policy":
        # 「那多久到账」这类追问，用上一轮的问题再检索一次
        hits = search_policies(_previous_user_text(state))
    update: dict[str, Any] = {"policy_hits": hits}
    if not hits:
        update["need_human"] = True
        update["handoff_reason"] = "政策未命中，避免说错"
    return update


def _db_of(config: dict[str, Any] | None):
    """从 LangGraph 运行时配置里取数据库会话（不放进 state，避免污染对话状态）。"""
    if not config:
        return None
    return (config.get("configurable") or {}).get("db")


def query_order_node(state: SupportState, config: dict[str, Any]) -> dict[str, Any]:
    result = order_detail(_db_of(config), state.get("user_id"), state.get("order_no"))
    return {"tool_name": "order_detail", "tool_result": result}


def query_logistics_node(state: SupportState, config: dict[str, Any]) -> dict[str, Any]:
    result = logistics_status(_db_of(config), state.get("user_id"), state.get("order_no"))
    return {"tool_name": "logistics_status", "tool_result": result}


def search_product_node(state: SupportState, config: dict[str, Any]) -> dict[str, Any]:
    keyword = state.get("product_keyword") or _extract_product_keyword(
        _last_user_text(state)
    )
    result = search_products(_db_of(config), keyword)
    return {"tool_name": "search_products", "tool_result": result}


def _extract_product_keyword(text: str) -> str:
    """去掉意图词、指代词和疑问词，剩下的当商品关键词。

    「卫龙辣条」这种品牌+品类要完整保留；「这个多少钱」清洗后应为空，
    由调用方回退到上一轮关键词。
    """
    noise = [
        "有没有", "有货吗", "有货", "多少钱", "什么价", "价格", "库存", "还有",
        "这个", "那个", "这款", "那款", "那单", "这单", "它",
        "多少", "几个", "几件", "怎么卖", "卖吗", "有木有", "还剩", "剩",
        "吗", "呢", "？", "?", "的", "那", "这", "个", "件", "种",
        "请问", "帮我", "查一下", "看看", "推荐一下", "一下", "能不能", "可以",
    ]
    keyword = text or ""
    for word in noise:
        keyword = keyword.replace(word, "")
    return keyword.strip()[:30]


def generate_node(state: SupportState) -> dict[str, Any]:
    if state.get("intent") == "human":
        # 情绪/投诉类不给模型发挥空间，直接走转人工话术
        return {"need_human": True, "handoff_reason": "用户要求人工或表达投诉"}

    result = get_llm().reply(state)
    need_human = bool(state.get("need_human"))
    reason = state.get("handoff_reason", "")

    text = _last_user_text(state)
    if any(word in text for word in HANDOFF_TRIGGERS):
        need_human, reason = True, "用户情绪激烈或提出投诉"

    return {
        "reply": result.text,
        "need_human": need_human,
        "handoff_reason": reason,
        "messages": [AIMessage(content=result.text)],
    }


def _route_after_generate(state: SupportState) -> str:
    return "handoff" if state.get("need_human") else END


def _ticket_summary(state: SupportState, limit: int = 400) -> str:
    lines = []
    for message in (state.get("messages") or [])[-6:]:
        role = "用户" if getattr(message, "type", "") in ("human", "user") else "客服"
        content = message.content if isinstance(message.content, str) else ""
        if content:
            lines.append(f"{role}：{content}")
    return "\n".join(lines)[:limit]


def handoff_node(state: SupportState, config: dict[str, Any]) -> dict[str, Any]:
    """建工单并给出转人工话术。db 缺失时降级为“已记录”，不阻断对话。"""
    reason = state.get("handoff_reason") or "用户要求人工"
    reply = state.get("reply") or ""

    db = _db_of(config)
    ticket_id: int | None = None
    if db is not None:
        try:
            from app.models.support_ticket import SupportTicket

            ticket = SupportTicket(
                session_id=state.get("session_id") or "",
                user_id=state.get("user_id"),
                order_no=state.get("order_no"),
                intent=state.get("intent") or "unknown",
                reason=reason[:255],
                summary=_ticket_summary(state),
                status="open",
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            ticket_id = ticket.id
        except Exception:  # noqa: BLE001 - 工单写失败不影响用户拿到回复
            db.rollback()

    if ticket_id:
        tail = f"已经帮你转人工（工单 #{ticket_id}），客服会在 9:00-22:00 之间联系你。"
    else:
        tail = "已经记下你的问题，客服稍后联系你。"

    if reply:
        # 生成过回复（例如政策没命中）时，保留前半段说明再补转人工
        final_text = f"{reply}\n\n{tail}"
    else:
        final_text = f"抱歉，这件事需要人工同事处理。{tail}"

    return {
        "reply": final_text,
        "need_human": True,
        "handoff_reason": reason,
        "ticket_id": ticket_id,
    }


def build_graph():
    graph = StateGraph(SupportState)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve_policy", retrieve_policy_node)
    graph.add_node("query_order", query_order_node)
    graph.add_node("query_logistics", query_logistics_node)
    graph.add_node("search_product", search_product_node)
    graph.add_node("generate", generate_node)
    graph.add_node("handoff", handoff_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        _route_by_intent,
        {
            "retrieve_policy": "retrieve_policy",
            "query_order": "query_order",
            "query_logistics": "query_logistics",
            "search_product": "search_product",
            "generate": "generate",
            "handoff": "handoff",
        },
    )
    for node in ("retrieve_policy", "query_order", "query_logistics", "search_product"):
        graph.add_edge(node, "generate")
    graph.add_conditional_edges(
        "generate", _route_after_generate, {"handoff": "handoff", END: END}
    )
    graph.add_edge("handoff", END)
    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


__all__ = ["build_graph", "get_graph", "INTENT_LABEL", "STATUS_TEXT"]
