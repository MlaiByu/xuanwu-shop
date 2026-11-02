from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.config import settings
from app.core.errors import BizException, ErrorCode
from app.core.responses import PageData, success
from app.database import get_db
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["管理端-订单"], dependencies=[Depends(get_current_admin)])


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise BizException(ErrorCode.PARAM_INVALID, "时间格式应为 ISO 8601") from None


@router.get("", summary="订单列表")
def admin_list_orders(
    order_no: str | None = Query(default=None),
    status: str | None = Query(default=None, description="逗号分隔多选"),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = order_service.admin_list_orders(
        db, order_no, status, _parse_time(start_time), _parse_time(end_time), page, size
    )
    return success(PageData.build(items, total, page, size))


@router.post("/{order_id}/ship", summary="发货")
def ship_order(order_id: int, db: Session = Depends(get_db)):
    order = order_service.admin_ship_order(db, order_id)
    return success({"id": order.id, "status": order.status})


@router.post("/{order_id}/expire", summary="触发超时取消（仅测试环境）")
def expire_order(order_id: int, db: Session = Depends(get_db)):
    if settings.is_production:
        raise BizException(ErrorCode.NOT_FOUND)
    order = order_service.force_expire_order(db, order_id)
    return success({"id": order.id, "status": order.status})
