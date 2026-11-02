"""密码哈希与 JWT（需求 §2.5）。

密码使用 bcrypt，cost 默认 12；任何响应体不得包含 hashed_password。
"""
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import settings

# 认证凭证 cookie 名：token 放 httpOnly cookie，JS 读不到、XSS 窃取不了（审查报告 M5）
COOKIE_NAME = "access_token"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(
        plain.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, is_admin: bool, token_version: int) -> tuple[str, int]:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "token_version": token_version,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int((expire - now).total_seconds())


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
