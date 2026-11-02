"""可插拔 LLM。

- 配了 `SUPPORT_LLM_API_KEY`：走 OpenAI 兼容接口（DeepSeek / 通义 / OpenAI 均可）。
- 没配或调用失败：回退到内置规则引擎，保证客服不因模型故障失联。

无论走哪条路，模型都只拿到“事实”（政策命中 + 工具结果），
不允许它自己查库或编造订单信息。
"""

import json
from dataclasses import dataclass

import httpx

from app.config import settings
from app.support.state import SupportState

SYSTEM_PROMPT = """你是「玄武商城」的在线客服「小玄」，说话像店里熟悉的店员：简洁、直接、有温度，不堆敬语。

必须遵守：
1. 只能依据【事实】回答。事实里没有的订单、金额、物流、库存，一律不编造。
2. 事实为空、用户要求赔偿/投诉/改地址/退款，或你不确定时，直接说会转人工处理，不要自行承诺。
3. 金额保留两位小数，订单号原样输出，不要省略。
4. 回答控制在 3-5 句；多条信息用「·」短列表，不用 Markdown 标题。
5. 不提"系统""接口""数据库""模型"这类实现细节。
6. 不要主动索要密码、验证码、银行卡号。

【语气示例】（只示范说话方式，具体数字以【事实】为准，不要照抄）
用户：这个还有货吗
助手：有货，能直接下单。要我把规格也发你吗？

用户：什么时候能到
助手：今天下单的话，48 小时内发出，顺丰大概 2-3 天到。

用户：能退吗
助手：7 天内可以退，不影响二次销售就行。拆封的食品和个护不支持无理由。

用户：太慢了，我要投诉
助手：这次确实让你等久了，抱歉。我已经转人工同事跟进，工单发你了，他会尽快联系你。"""


@dataclass
class LLMResult:
    text: str
    source: str  # llm / rule / fallback


def _format_orders(orders: list[dict]) -> str:
    lines = []
    for order in orders:
        lines.append(
            f"· {order['order_no']}（{order['created_at']}）{order['status_text']}"
            f" · ¥{order['total_amount']} · {order['item_summary']}"
        )
    return "\n".join(lines)


def _rule_reply(state: SupportState) -> str:
    """无模型时的兜底话术：按意图把事实翻译成人话。"""
    intent = state.get("intent") or "chitchat"
    tool = state.get("tool_result") or {}
    nickname = state.get("nickname")

    if intent == "order":
        if not tool.get("ok"):
            reason = tool.get("reason")
            if reason == "anonymous":
                return "查订单需要先登录。登录后点右下角这里，我可以直接帮你查最近的单子和物流。"
            if reason == "empty":
                return "这个账号下还没有订单。选好商品下单后，我就能帮你跟进发货和物流了。"
            return f"{tool.get('message', '没查到这笔订单')}。麻烦核对一下单号，或者把手机号后四位发我，我转人工帮你查。"

        data = tool.get("data") or {}
        if "orders" in data:
            body = _format_orders(data["orders"])
            return f"帮你查到最近这几笔：\n{body}\n要看哪一单的详情或物流，把单号发我就行。"
        items = data.get("items") or []
        item_text = "、".join(f"{item['name']} × {item['quantity']}" for item in items[:3])
        return (
            f"订单 {data.get('order_no')} 现在是「{data.get('status_text')}」，"
            f"实付 ¥{data.get('total_amount')}。\n"
            f"商品：{item_text}。\n{data.get('hint', '')}"
        )

    if intent == "logistics":
        if not tool.get("ok"):
            reason = tool.get("reason")
            if reason == "anonymous":
                return "查物流需要先登录，登录后把单号发我，我直接告诉你到哪了。"
            return "这笔单子我没查到，可能单号不对或者不在这个账号下。要转人工帮你查吗？"
        data = tool.get("data") or {}
        if data.get("status") == "shipped":
            arrival = f"，预计 {data['expected_arrival']} 前送达" if data.get("expected_arrival") else ""
            return f"订单 {data['order_no']} 已经发出了{arrival}。{data.get('hint', '')}"
        return f"订单 {data['order_no']} 目前是「{data.get('status_text')}」。{data.get('hint', '')}"

    if intent == "product":
        if not tool.get("ok"):
            if tool.get("reason") == "empty_keyword":
                return "你想问哪件商品？说个名字或型号就行，比如「卫龙辣条」。"
            return f"{tool.get('message', '没找到相关商品')}。你可以换个关键词，或者告诉我用途和预算，我帮你挑。"
        products = (tool.get("data") or {}).get("products") or []
        if len(products) == 1:
            item = products[0]
            # 追问场景用「这款」，避免出现「这件卫龙辣条 现在…」这种别扭的拼接
            subject = "这款" if state.get("prev_intent") == "product" else item["name"]
            return (
                f"{subject}现在 ¥{item['price']}，库存 {item['stock']} 件，"
                "可以直接下单。要我把规格也发你吗？"
            )
        lines = [
            f"· {item['name']} · ¥{item['price']} · 库存 {item['stock']}"
            for item in products
        ]
        return "找到这几件：\n" + "\n".join(lines) + "\n要哪个的详细参数？"

    if intent == "policy":
        hits = state.get("policy_hits") or []
        if hits:
            return "\n".join(f"{item['title']}：{item['answer']}" for item in hits[:2])
        return "这个政策我不太确定，别给你说错了。我转人工让同事跟你确认一下？"

    if intent == "human":
        return "抱歉给你添麻烦了，这件事我转人工同事跟进，他会在 9:00-22:00 之间联系你。"

    if intent == "chitchat":
        # 已经聊过几轮还认不出意图，就别再念一遍自我介绍了
        user_turns = sum(
            1
            for message in (state.get("messages") or [])
            if getattr(message, "type", "") in ("human", "user")
        )
        if user_turns > 1:
            return (
                "没太听懂。你是想问商品、订单，还是退换货？"
                "直接说商品名也行，比如「卫龙辣条」。"
            )

    name = f"你好，{nickname}。" if nickname else ""
    return (
        f"{name}我是玄武商城的客服小玄。"
        "可以帮你查订单和物流、确认退换货和运费政策、看看商品有没有货。"
        "直接说需求就行，比如「我的订单到哪了」。"
    )


class SupportLLM:
    def __init__(self) -> None:
        self.base_url = settings.support_llm_base_url.rstrip("/")
        self.api_key = settings.support_llm_api_key.strip()
        self.model = settings.support_llm_model
        self.temperature = settings.support_llm_temperature
        self.timeout = settings.support_llm_timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @property
    def mode(self) -> str:
        return "llm" if self.enabled else "rule"

    def _facts(self, state: SupportState) -> str:
        payload = {
            "意图": state.get("intent"),
            "用户昵称": state.get("nickname"),
            "是否登录": bool(state.get("user_id")),
            "会话上下文": {
                "上一轮意图": state.get("prev_intent"),
                "上一轮商品": state.get("prev_product_keyword"),
                "上一轮订单号": state.get("prev_order_no"),
                "本轮商品关键词": state.get("product_keyword"),
            },
            "政策命中": [
                {"标题": item["title"], "答案": item["answer"]}
                for item in (state.get("policy_hits") or [])
            ],
            "工具结果": state.get("tool_result"),
        }
        text = json.dumps(payload, ensure_ascii=False, default=str)
        return text[:4000]

    def _call(self, state: SupportState) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        history = state.get("messages") or []
        for message in history[-8:]:
            role = "user" if message.type in ("human", "user") else "assistant"
            content = message.content if isinstance(message.content, str) else str(message.content)
            if content:
                messages.append({"role": role, "content": content})
        messages.append(
            {
                "role": "user",
                "content": f"【事实】\n{self._facts(state)}\n\n请依据以上事实回答用户最后一条消息。",
            }
        )

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 600,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    def reply(self, state: SupportState) -> LLMResult:
        if not self.enabled:
            return LLMResult(_rule_reply(state), "rule")
        try:
            text = self._call(state)
            if not text:
                raise ValueError("empty completion")
            return LLMResult(text, "llm")
        except Exception:  # noqa: BLE001 - 模型故障必须降级而不是让客服失联
            return LLMResult(_rule_reply(state), "fallback")


_llm: SupportLLM | None = None


def get_llm() -> SupportLLM:
    global _llm
    if _llm is None:
        _llm = SupportLLM()
    return _llm
