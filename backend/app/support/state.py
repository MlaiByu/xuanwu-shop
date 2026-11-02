"""客服会话状态。

设计原则：**事实由工具产出，语言模型只负责措辞**。
因此状态里显式区分 intent / tool_result / policy_hits，生成节点只能读这些字段，
不允许模型自己查库或脑补订单信息。
"""

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class SupportState(TypedDict, total=False):
    # 对话消息（add_messages 保证多轮追加而不是覆盖）
    messages: Annotated[list, add_messages]

    # 会话与身份：user_id 只由后端注入，绝不从用户输入解析
    session_id: str
    user_id: int | None
    nickname: str | None

    # 意图与置信度
    intent: str
    confidence: float

    # 会话上下文（从历史里回算，用于处理「那这个呢」「多少钱」这类追问）
    prev_intent: str | None
    prev_product_keyword: str | None
    prev_order_no: str | None
    product_keyword: str | None

    # 事实来源
    tool_name: str | None
    tool_result: dict[str, Any] | None
    policy_hits: list[dict[str, Any]]

    # 关联订单（工具解析出的单号，或用户直接报的单号）
    order_no: str | None

    # 是否需要转人工
    need_human: bool
    handoff_reason: str
    ticket_id: int | None

    # 最终回复
    reply: str
