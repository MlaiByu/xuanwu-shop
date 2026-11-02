from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

TICKET_STATUSES = ("open", "processing", "closed")


class SupportTicket(TimestampMixin, Base):
    """转人工工单。

    智能客服判断需要人工介入时写入：保留会话、意图、触发原因与对话摘要，
    客服后台据此接手。session_id 与前端会话一一对应，便于回看完整对话。
    """

    __tablename__ = "support_tickets"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','processing','closed')",
            name="ck_support_tickets_status",
        ),
        Index("ix_support_tickets_user_created", "user_id", "created_at"),
        Index("ix_support_tickets_session", "session_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 游客也能咨询，因此允许为空；账号被删后工单仍保留（SET NULL）
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    order_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intent: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
