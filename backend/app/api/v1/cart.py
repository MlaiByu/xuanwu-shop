from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.responses import success
from app.database import get_db
from app.models.user import User
from app.schemas.cart import CartAdd, CartUpdate
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["购物车"], dependencies=[Depends(get_current_user)])


@router.get("", summary="购物车列表")
def list_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success(cart_service.list_cart(db, user))


@router.post("", summary="加入购物车")
def add_to_cart(payload: CartAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success(cart_service.add_to_cart(db, user, payload))


@router.patch("/{cart_item_id}", summary="修改数量")
def update_quantity(
    cart_item_id: int, payload: CartUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return success(cart_service.update_quantity(db, user, cart_item_id, payload))


@router.delete("/{cart_item_id}", summary="删除购物车项")
def remove_from_cart(
    cart_item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    cart_service.remove_from_cart(db, user, cart_item_id)
    return success()
