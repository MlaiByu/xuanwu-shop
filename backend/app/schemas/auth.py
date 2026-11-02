import re
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr = Field(max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=64)
    nickname: str | None = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        value = value.strip()
        if not re.fullmatch(r"1[3-9]\d{9}", value):
            raise ValueError("手机号格式不正确")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value)):
            raise ValueError("密码须同时包含字母与数字")
        return value

    @field_validator("nickname")
    @classmethod
    def normalize_nickname(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class LoginRequest(BaseModel):
    """支持邮箱或手机号作为账号。"""

    account: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=64)


class UserOut(BaseModel):
    """对外用户模型：绝不包含 hashed_password。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    phone: str | None
    nickname: str
    is_admin: bool
    role: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        # 防御性兜底：万一驱动返回 naive datetime，统一按 UTC 补全时区，保证输出带偏移
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value)):
            raise ValueError("密码须同时包含字母与数字")
        return value


class AdminCreateRequest(BaseModel):
    """超级管理员创建普通管理员。"""

    email: EmailStr = Field(max_length=120)
    password: str = Field(min_length=8, max_length=64)
    nickname: str | None = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value)):
            raise ValueError("密码须同时包含字母与数字")
        return value
