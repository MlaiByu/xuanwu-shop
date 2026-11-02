"""商家入驻审核接口（超级管理员专属）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_super_admin
from app.core.responses import success
from app.database import get_db
from app.schemas.merchant import MerchantRejectRequest
from app.services import merchant_service

router = APIRouter(
    prefix="/merchants",
    tags=["管理端-商家审核"],
    dependencies=[Depends(get_current_super_admin)],
)


@router.get("", summary="商家列表")
def list_merchants(
    status: str | None = Query(default="all"),
    db: Session = Depends(get_db),
):
    return success(merchant_service.list_merchants(db, None if status == "all" else status))


@router.post("/{merchant_id}/approve", summary="通过入驻")
def approve_merchant(merchant_id: int, db: Session = Depends(get_db)):
    merchant = merchant_service.approve(db, merchant_id)
    return success({"id": merchant.id, "status": merchant.status})


@router.post("/{merchant_id}/reject", summary="驳回入驻")
def reject_merchant(merchant_id: int, payload: MerchantRejectRequest, db: Session = Depends(get_db)):
    merchant = merchant_service.reject(db, merchant_id, payload.remark)
    return success({"id": merchant.id, "status": merchant.status})
