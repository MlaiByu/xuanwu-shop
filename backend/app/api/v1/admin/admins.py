"""管理员管理接口（超级管理员专属）。"""
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_super_admin
from app.core.responses import success
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AdminCreateRequest, UserOut
from app.services import admin_service

router = APIRouter(
    prefix="/admins",
    tags=["管理端-管理员"],
    dependencies=[Depends(get_current_super_admin)],
)


@router.get("", summary="管理员列表")
def list_admins(db: Session = Depends(get_db)):
    admins = admin_service.list_admins(db)
    return success([UserOut.model_validate(a) for a in admins])


@router.post("", summary="创建普通管理员")
def create_admin(payload: AdminCreateRequest, db: Session = Depends(get_db)):
    admin = admin_service.create_admin(db, payload)
    return success(UserOut.model_validate(admin))


@router.patch("/{admin_id}/status", summary="禁用/启用管理员")
def set_admin_status(
    admin_id: int,
    payload: dict = Body(...),
    operator: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    is_active = bool(payload.get("is_active", True))
    admin = admin_service.set_admin_status(db, admin_id, is_active, operator)
    return success(UserOut.model_validate(admin))


@router.delete("/{admin_id}", summary="删除管理员")
def delete_admin(
    admin_id: int,
    operator: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    admin_service.delete_admin(db, admin_id, operator)
    return success()
