"""商家业务（ABC 三端 B 端）：入驻、审核、商品、订单。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.core.money import format_price
from app.models.merchant import Merchant
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.merchant import MerchantOut
from app.schemas.order import OrderListItem
from app.schemas.product import ProductAdminItem, ProductCreate, ProductUpdate
from app.services import product_service

# ---------- 入驻与审核 ----------

def apply(db: Session, user: User, shop_name: str) -> Merchant:
    existing = db.scalar(select(Merchant).where(Merchant.user_id == user.id))
    if existing:
        if existing.status == Merchant.STATUS_APPROVED:
            raise BizException(ErrorCode.ALREADY_EXISTS, "已是入驻商家")
        raise BizException(ErrorCode.ALREADY_EXISTS, "已提交过入驻申请，请等待审核")
    merchant = Merchant(user_id=user.id, shop_name=shop_name, status=Merchant.STATUS_PENDING)
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def list_merchants(db: Session, status: str | None) -> list[MerchantOut]:
    query = select(Merchant)
    if status and status != "all":
        query = query.where(Merchant.status == status)
    merchants = db.scalars(query.order_by(Merchant.id)).all()
    user_map = {}
    if merchants:
        users = db.scalars(select(User).where(User.id.in_([m.user_id for m in merchants]))).all()
        user_map = {u.id: u for u in users}
    return [
        MerchantOut(
            id=m.id,
            user_id=m.user_id,
            shop_name=m.shop_name,
            status=m.status,
            audit_remark=m.audit_remark,
            user_email=user_map[m.user_id].email if m.user_id in user_map else None,
            created_at=m.created_at,
        )
        for m in merchants
    ]


def approve(db: Session, merchant_id: int) -> Merchant:
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise BizException(ErrorCode.NOT_FOUND)
    if merchant.status != Merchant.STATUS_PENDING:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待审核商家可操作")
    merchant.status = Merchant.STATUS_APPROVED
    user = db.get(User, merchant.user_id)
    if user is not None:
        user.role = User.ROLE_MERCHANT
    db.commit()
    db.refresh(merchant)
    return merchant


def reject(db: Session, merchant_id: int, remark: str) -> Merchant:
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise BizException(ErrorCode.NOT_FOUND)
    if merchant.status != Merchant.STATUS_PENDING:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待审核商家可操作")
    merchant.status = Merchant.STATUS_REJECTED
    merchant.audit_remark = remark
    db.commit()
    db.refresh(merchant)
    return merchant


def get_profile(db: Session, merchant: Merchant) -> MerchantOut:
    user = db.get(User, merchant.user_id)
    return MerchantOut(
        id=merchant.id,
        user_id=merchant.user_id,
        shop_name=merchant.shop_name,
        status=merchant.status,
        audit_remark=merchant.audit_remark,
        user_email=user.email if user else None,
        created_at=merchant.created_at,
    )


# ---------- 商家商品 ----------

def _get_owned_product(db: Session, merchant: Merchant, product_id: int) -> Product:
    product = db.get(Product, product_id)
    # 越权一律 404，不暴露商品存在性
    if product is None or product.merchant_id != merchant.id:
        raise BizException(ErrorCode.NOT_FOUND, "商品不存在")
    return product


def list_products(db: Session, merchant: Merchant) -> list[ProductAdminItem]:
    products = db.scalars(
        select(Product).where(Product.merchant_id == merchant.id).order_by(Product.id.desc())
    ).all()
    return product_service.build_admin_items(db, products)


def create_product(db: Session, merchant: Merchant, payload: ProductCreate) -> Product:
    return product_service.create_product(db, payload, merchant_id=merchant.id)


def update_product(db: Session, merchant: Merchant, product_id: int, payload: ProductUpdate) -> Product:
    _get_owned_product(db, merchant, product_id)
    return product_service.update_product(db, product_id, payload)


def delete_product(db: Session, merchant: Merchant, product_id: int) -> None:
    product = _get_owned_product(db, merchant, product_id)
    has_orders = db.scalar(
        select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)
    )
    if has_orders:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "该商品存在历史订单，请改为下架")
    db.delete(product)
    db.commit()


def set_product_status(db: Session, merchant: Merchant, product_id: int, is_active: bool) -> Product:
    product = _get_owned_product(db, merchant, product_id)
    product.is_active = is_active
    db.commit()
    db.refresh(product)
    return product


# ---------- 商家订单 ----------

def list_orders(
    db: Session, merchant: Merchant, status: str | None, page: int, size: int
) -> tuple[list[OrderListItem], int]:
    # 用子查询定位含本商家商品的订单，避免把 order_id 全量加载进内存
    order_ids_sq = (
        select(OrderItem.order_id).where(OrderItem.merchant_id == merchant.id).distinct()
    )
    query = select(Order).where(Order.id.in_(order_ids_sq))
    if status and status != "all":
        query = query.where(Order.status == status)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    orders = db.scalars(
        query.order_by(Order.created_at.desc(), Order.id.desc()).offset((page - 1) * size).limit(size)
    ).all()

    items = []
    for order in orders:
        mine = [i for i in order.items if i.merchant_id == merchant.id]
        first = mine[0] if mine else None
        items.append(
            OrderListItem(
                id=order.id,
                order_no=order.order_no,
                status=order.status,
                total_amount=format_price(sum(i.price * i.quantity for i in mine)),
                created_at=order.created_at,
                total_quantity=sum(i.quantity for i in mine),
                preview_image=first.main_image if first else None,
                preview_name=first.product_name if first else None,
            )
        )
    return items, total
