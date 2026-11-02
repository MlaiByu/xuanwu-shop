from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    # 角色枚举（ABC 三端）：C 端买家 / B 端商家 / A 端管理员 / A 端超级管理员
    ROLE_CUSTOMER = "customer"
    ROLE_MERCHANT = "merchant"
    ROLE_ADMIN = "admin"
    ROLE_SUPER_ADMIN = "super_admin"
    ADMIN_ROLES = (ROLE_ADMIN, ROLE_SUPER_ADMIN)

    id: Mapped[int] = mapped_column(primary_key=True)
    # 存储时统一小写，避免大小写变体绕过唯一约束
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(16), default=ROLE_CUSTOMER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 凭证版本号：改密码 / 封禁时 +1，已签发的旧 token 立即失效。
    # JWT 里存版本、请求时比对，实现"改密/封号即踢下线"（审查报告 M1）。
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
