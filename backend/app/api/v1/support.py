"""智能客服接口。

- POST /support/sessions        建会话（游客可用）
- POST /support/chat            SSE 流式对话
- GET  /support/meta            模型模式 + 快捷问题
- GET  /support/sessions/{id}   会话历史（刷新后恢复）
- GET  /support/tickets         我的工单
"""

import json
from typing import Any, Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.core.responses import success
from app.database import SessionLocal, get_db
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.support.llm import get_llm
from app.support.policies import policy_titles
from app.support.service import SupportService

router = APIRouter(prefix="/support", tags=["智能客服"])

QUICK_QUESTIONS = [
    "我的订单到哪了",
    "怎么申请退货",
    "运费怎么算",
    "能开发票吗",
    "我要转人工",
]


class ChatIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=500)


class ChatOut(BaseModel):
    pass


@router.get("/meta", summary="客服元信息")
def meta():
    llm = get_llm()
    return success(
        {
            "mode": llm.mode,
            "model": llm.model if llm.enabled else "内置规则引擎",
            "quick_questions": QUICK_QUESTIONS,
            "policy_topics": policy_titles(),
        }
    )


@router.post("/sessions", summary="创建客服会话")
def create_session():
    # 这里不需要数据库，传 None 即可（stream 时才注入会话）
    return success({"session_id": SupportService(None).create_session()})


@router.post("/chat", summary="流式对话（SSE）")
def chat(payload: ChatIn, user: User | None = Depends(get_current_user_optional)):
    # 先把身份取成标量：生成器在请求上下文结束后才执行，不能持有 ORM 对象
    user_id = user.id if user else None
    nickname = (user.nickname or user.email.split("@")[0]) if user else None

    def event_stream() -> Iterator[str]:
        db = SessionLocal()
        try:
            service = SupportService(db)
            for event, data in service.stream(
                payload.session_id, payload.message, user_id=user_id, nickname=nickname
            ):
                yield _sse(event, data)
        except Exception as exc:  # noqa: BLE001 - 任何异常都要给前端一个结束事件
            yield _sse("error", {"message": str(exc)[:200]})
        finally:
            db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/messages", summary="会话历史")
def session_messages(session_id: str):
    return success({"messages": SupportService(None).history(session_id)})


@router.get("/tickets", summary="我的工单")
def my_tickets(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    rows = db.scalars(
        select(SupportTicket)
        .where(SupportTicket.user_id == user.id)
        .order_by(SupportTicket.created_at.desc())
        .limit(20)
    ).all()
    return success(
        [
            {
                "id": row.id,
                "order_no": row.order_no,
                "intent": row.intent,
                "reason": row.reason,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    )


def _sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps({"event": event, "data": data}, ensure_ascii=False)
    return f"data: {payload}\n\n"
