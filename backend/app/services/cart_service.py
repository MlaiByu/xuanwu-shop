"""购物车业务（需求 FR-U-05）。"""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.core.money import format_price
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.sku import Sku
from app.models.user import User
from app.schemas.cart import CartAdd, CartItemOut, CartSummary, CartUpdate


def _get_sku_checked(db: Session, sku_id: int) -> tuple[Sku, Product]:
    sku = db.get(Sku, sku_id)
    if sku is None:
        # 不存在/已删除的 SKU 归 404，与"停售/下架"的 40902 区分（S-02、AC-U04-5）
        raise BizException(ErrorCode.NOT_FOUND, "商品规格不存在")
    if not sku.is_active:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "商品规格已停售")
    product = db.get(Product, sku.product_id)
    if product is None or not product.is_active:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "商品已下架")
    return sku, product


def _to_out(item: CartItem, sku: Sku | None, product: Product | None) -> CartItemOut:
    if sku is None or product is None:
        # sku 被删除时 cart_item 会级联删除，此处仅兜底
        price = Decimal("0")
        return CartItemOut(
            id=item.id,
            sku_id=item.sku_id,
            product_id=0,
            product_name="商品已失效",
            main_image="",
            attrs={},
            price=format_price(price),
            quantity=item.quantity,
            stock=0,
            is_valid=False,
            subtotal=format_price(price * item.quantity),
        )

    price = sku.price
    return CartItemOut(
        id=item.id,
        sku_id=item.sku_id,
        product_id=product.id,
        product_name=product.name,
        main_image=product.main_image,
        attrs=sku.attrs or {},
        price=format_price(price),
        quantity=item.quantity,
        stock=sku.stock,
        is_valid=product.is_active and sku.is_active and sku.stock > 0,
        subtotal=format_price(price * item.quantity),
    )


def list_cart(db: Session, user: User) -> CartSummary:
    rows = db.execute(
        select(CartItem, Sku, Product)
        .outerjoin(Sku, Sku.id == CartItem.sku_id)
        .outerjoin(Product, Product.id == Sku.product_id)
        .where(CartItem.user_id == user.id)
        .order_by(CartItem.id)
    ).all()
    out_items = [_to_out(item, sku, product) for item, sku, product in rows]
    valid = [i for i in out_items if i.is_valid]
    total_quantity = sum(i.quantity for i in valid)
    total = sum(Decimal(i.price) * i.quantity for i in valid)
    return CartSummary(items=out_items, total_quantity=total_quantity, total_amount=format_price(total))


def add_to_cart(db: Session, user: User, payload: CartAdd) -> CartItemOut:
    sku, product = _get_sku_checked(db, payload.sku_id)
    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.sku_id == payload.sku_id)
    )
    new_quantity = (item.quantity if item else 0) + payload.quantity
    if new_quantity > sku.stock:
        raise BizException(ErrorCode.STOCK_NOT_ENOUGH, "库存不足")
    if item is None:
        item = CartItem(user_id=user.id, sku_id=payload.sku_id, quantity=payload.quantity)
        db.add(item)
    else:
        item.quantity = new_quantity
    db.commit()
    db.refresh(item)
    return _to_out(item, sku, product)


def update_quantity(db: Session, user: User, cart_item_id: int, payload: CartUpdate) -> CartItemOut:
    item = db.scalar(
        select(CartItem).where(CartItem.id == cart_item_id, CartItem.user_id == user.id)
    )
    if item is None:
        raise BizException(ErrorCode.NOT_FOUND)
    sku, product = _get_sku_checked(db, item.sku_id)
    if payload.quantity > sku.stock:
        raise BizException(ErrorCode.STOCK_NOT_ENOUGH, "库存不足")
    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)
    return _to_out(item, sku, product)


def remove_from_cart(db: Session, user: User, cart_item_id: int) -> None:
    item = db.scalar(
        select(CartItem).where(CartItem.id == cart_item_id, CartItem.user_id == user.id)
    )
    if item is None:
        raise BizException(ErrorCode.NOT_FOUND)
    db.delete(item)
    db.commit()
