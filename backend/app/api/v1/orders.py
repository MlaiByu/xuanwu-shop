from typing import Literal

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.responses import PageData, success
from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["订单"], dependencies=[Depends(get_current_user)])

OrderStatus = Literal["all", "pending", "paid", "shipped", "completed", "cancelled"]


@router.get("/checkout", summary="结算页预览")
def checkout_preview(
    cart_item_ids: str = Query(description="逗号分隔的购物车项 id"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = [int(x) for x in cart_item_ids.split(",") if x.strip()]
    if not ids:
        return success(order_service.checkout_preview(db, user, []))
    return success(order_service.checkout_preview(db, user, ids))


@router.post("", summary="提交订单")
def create_order(
    payload: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    order = order_service.create_order(db, user, payload, idempotency_key)
    return success(
        {"id": order.id, "order_no": order.order_no, "status": order.status, "total_amount": str(order.total_amount)}
    )


@router.get("", summary="我的订单列表")
def list_orders(
    status: OrderStatus = Query(default="all"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = order_service.list_orders(db, user, None if status == "all" else status, page, size)
    return success(PageData.build(items, total, page, size))


@router.get("/{order_id}", summary="订单详情")
def get_order_detail(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success(order_service.get_order_detail(db, user, order_id))


@router.post("/{order_id}/pay", summary="模拟支付")
def pay_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = order_service.pay_order(db, user, order_id)
    return success({"id": order.id, "status": order.status})


@router.post("/{order_id}/cancel", summary="取消订单")
def cancel_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = order_service.cancel_order(db, user, order_id)
    return success({"id": order.id, "status": order.status})


@router.post("/{order_id}/confirm", summary="确认收货")
def confirm_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = order_service.confirm_order(db, user, order_id)
    return success({"id": order.id, "status": order.status})
