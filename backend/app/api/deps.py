"""依赖注入：认证与角色校验（需求 §4 四层校验的 L1、L2）。"""
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.core.security import COOKIE_NAME, decode_access_token
from app.database import get_db
from app.models.merchant import Merchant
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False, description="JWT，格式：Bearer <token>")


def _extract_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None
) -> str | None:
    """优先取 httpOnly cookie，其次兼容 Authorization 头（供 curl / 脚本调试）。"""
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        return cookie
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_token(request, credentials)
    if token is None:
        raise BizException(ErrorCode.UNAUTHENTICATED)

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise BizException(ErrorCode.TOKEN_INVALID, "登录已过期，请重新登录") from None
    except jwt.InvalidTokenError:
        raise BizException(ErrorCode.TOKEN_INVALID, "登录凭证无效") from None

    subject = payload.get("sub")
    if not subject:
        raise BizException(ErrorCode.TOKEN_INVALID, "登录凭证无效")

    # sub 必须是数字字符串；伪造 token 无法通过签名，但防御性兜住非数字 sub，
    # 避免 int() 抛 ValueError 变成 500 而不是 401（审查报告 m1）。
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise BizException(ErrorCode.TOKEN_INVALID, "登录凭证无效") from None

    user = db.get(User, user_id)
    # 停用账号即刻失效（原实现靠前端缓存判断，停用后 token 仍能撑满有效期）
    if user is None or not user.is_active:
        raise BizException(ErrorCode.TOKEN_INVALID, "账号不存在或已停用")
    # 改密码 / 封禁会 +1 token_version，旧 token 立即作废（审查报告 M1）
    if payload.get("token_version", 0) != user.token_version:
        raise BizException(ErrorCode.TOKEN_INVALID, "登录凭证已失效，请重新登录")
    return user


def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """可选的登录态：用于游客也能用的接口（如智能客服）。

    与 get_current_user 的区别是：token 缺失或无效时返回 None，不抛 401。
    校验逻辑保持一致（停用账号、token_version 失效都要挡住）。
    """
    token = _extract_token(request, credentials)
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub") or "")
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    if payload.get("token_version", 0) != user.token_version:
        return None
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise BizException(ErrorCode.FORBIDDEN, "需要管理员权限")
    return user


def get_current_super_admin(user: User = Depends(get_current_user)) -> User:
    """超级管理员（A 端最高权限），独占「管管理员」与「商家审核」。"""
    if user.role != User.ROLE_SUPER_ADMIN:
        raise BizException(ErrorCode.FORBIDDEN, "需要超级管理员权限")
    return user


def get_current_merchant(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Merchant:
    """商家（B 端），须已入驻且审核通过。"""
    if user.role != User.ROLE_MERCHANT:
        raise BizException(ErrorCode.FORBIDDEN, "需要商家权限")
    merchant = db.scalar(select(Merchant).where(Merchant.user_id == user.id))
    if merchant is None or merchant.status != Merchant.STATUS_APPROVED:
        raise BizException(ErrorCode.FORBIDDEN, "商家未入驻或未通过审核")
    return merchant
