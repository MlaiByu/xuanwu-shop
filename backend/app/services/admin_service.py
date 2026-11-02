"""管理员管理业务（超级管理员专属，ABC 三端 A 端）。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AdminCreateRequest


def list_admins(db: Session) -> list[User]:
    return list(
        db.scalars(select(User).where(User.is_admin.is_(True)).order_by(User.id)).all()
    )


def create_admin(db: Session, payload: AdminCreateRequest) -> User:
    repo = UserRepository(db)
    if repo.email_or_phone_exists(payload.email, None) == "email":
        raise BizException(ErrorCode.ALREADY_EXISTS, "该邮箱已注册")
    nickname = payload.nickname or payload.email.split("@")[0][:20]
    return repo.create(
        email=payload.email,
        phone=None,
        hashed_password=hash_password(payload.password),
        nickname=nickname,
        is_admin=True,
        role=User.ROLE_ADMIN,
    )


def _get_target_admin(db: Session, admin_id: int, operator: User) -> User:
    target = db.get(User, admin_id)
    if target is None or not target.is_admin:
        raise BizException(ErrorCode.NOT_FOUND, "管理员不存在")
    if target.role == User.ROLE_SUPER_ADMIN:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "不能操作超级管理员")
    if target.id == operator.id:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "不能操作自己的账号")
    return target


def set_admin_status(db: Session, admin_id: int, is_active: bool, operator: User) -> User:
    target = _get_target_admin(db, admin_id, operator)
    target.is_active = is_active
    # 封禁/解封都让已签发的 token 立即失效，强制重新登录（M1）
    target.token_version += 1
    db.commit()
    db.refresh(target)
    return target


def delete_admin(db: Session, admin_id: int, operator: User) -> None:
    target = _get_target_admin(db, admin_id, operator)
    db.delete(target)
    db.commit()
