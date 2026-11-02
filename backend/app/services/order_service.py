"""订单与状态机业务（需求 FR-U-06/07/08、FR-A-03、§5）。

核心不变量（§5.5）：
- 下单扣库存使用条件更新，禁止"先查后改"；
- 状态流转全部条件更新，天然幂等；
- 金额只由后端用 Decimal 计算。
"""
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import BizException, ErrorCode
from app.core.money import format_price
from app.models.address import Address
from app.models.cart_item import CartItem
from app.models.idempotency_key import IdempotencyKey
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sku import Sku
from app.models.user import User
from app.schemas.address import AddressOut
from app.schemas.order import (
    AddressSnapshot,
    AdminOrderListItem,
    CheckoutItem,
    CheckoutPreview,
    OrderCreate,
    OrderDetail,
    OrderItemOut,
    OrderListItem,
    TimelineEvent,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _exec_update(db: Session, stmt) -> CursorResult[Any]:
    """执行 INSERT/UPDATE/DELETE 并返回 CursorResult。

    SQLAlchemy 的 Session.execute 类型标注为 Result（无 rowcount），
    实际对 DML 返回 CursorResult（有 rowcount），此处显式收窄类型。
    """
    return db.execute(stmt)  # type: ignore[return-value]


def _build_order_no(created_at: datetime, order_id: int) -> str:
    """订单号 = 时间戳 + 自增主键，天然唯一，无需先查后插、也无并发撞号。

    原先用「SELECT 检查再 INSERT」，并发下同秒同随机串会撞唯一约束，
    被兜底成笼统 409；用 id 作后缀后，id 全局唯一即单号全局唯一（审查报告 m2）。
    """
    return f"{created_at.strftime('%Y%m%d%H%M%S')}{order_id:06d}"


def _payload_hash(payload: OrderCreate) -> str:
    canonical = json.dumps(
        {
            "address_id": payload.address_id,
            "cart_item_ids": sorted(payload.cart_item_ids),
            "remark": payload.remark,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_owned_order(db: Session, user: User, order_id: int) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == user.id))
    if order is None:
        raise BizException(ErrorCode.NOT_FOUND)
    return order


def _build_snapshot(address) -> AddressSnapshot:
    return AddressSnapshot(
        receiver=address.receiver,
        phone=address.phone,
        province=address.province,
        city=address.city,
        district=address.district,
        detail=address.detail,
    )


def _build_timeline(order: Order) -> list[TimelineEvent]:
    events = [
        ("下单", order.created_at),
        ("支付成功", order.paid_at),
        ("已发货", order.shipped_at),
        ("交易完成", order.completed_at),
        ("已取消", order.cancelled_at),
    ]
    return [TimelineEvent(label=label, time=ts) for label, ts in events if ts is not None]


def _to_item_out(item: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        id=item.id,
        product_name=item.product_name,
        sku_attrs=item.sku_attrs or {},
        main_image=item.main_image,
        price=format_price(item.price),
        quantity=item.quantity,
        subtotal=format_price(item.price * item.quantity),
    )


# ---------- 结算预览 ----------

def checkout_preview(db: Session, user: User, cart_item_ids: list[int]) -> CheckoutPreview:
    items = db.scalars(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.id.in_(cart_item_ids))
    ).all()
    if len(items) != len(set(cart_item_ids)):
        raise BizException(ErrorCode.NOT_FOUND, "部分购物车项不存在")

    address = db.scalar(
        select(Address).where(Address.user_id == user.id, Address.is_default.is_(True))
    )

    checkout_items: list[CheckoutItem] = []
    valid_subtotal = Decimal("0")
    valid_qty = 0
    for item in items:
        sku = db.get(Sku, item.sku_id)
        product = db.get(Product, sku.product_id) if sku else None
        is_valid = bool(sku and product and product.is_active and sku.is_active and sku.stock >= item.quantity)
        subtotal = (sku.price * item.quantity) if sku else Decimal("0")
        checkout_items.append(
            CheckoutItem(
                cart_item_id=item.id,
                product_name=product.name if product else "商品已失效",
                sku_attrs=sku.attrs if sku else {},
                main_image=product.main_image if product else "",
                price=format_price(sku.price) if sku else "0.00",
                quantity=item.quantity,
                subtotal=format_price(subtotal),
                is_valid=is_valid,
            )
        )
        if is_valid:
            valid_subtotal += subtotal
            valid_qty += item.quantity

    return CheckoutPreview(
        address=AddressOut.model_validate(address).model_dump() if address else None,
        items=checkout_items,
        total_quantity=valid_qty,
        total_amount=format_price(valid_subtotal),
    )


# ---------- 下单（核心事务） ----------

def create_order(
    db: Session, user: User, payload: OrderCreate, idempotency_key: str | None = None
) -> Order:
    # 幂等：先原子占位（PG ON CONFLICT），消除"检查-插入"之间的并发竞态（CC-04）
    request_hash = _payload_hash(payload) if idempotency_key else None
    if idempotency_key:
        stmt = (
            pg_insert(IdempotencyKey)
            .values(user_id=user.id, key=idempotency_key, request_hash=request_hash)
            .on_conflict_do_nothing(index_elements=["user_id", "key"])
            .returning(IdempotencyKey.id)
        )
        # 显式 RETURNING 时，插入成功返回一行、冲突（DO NOTHING）返回 0 行，
        # 用 first() 判断占位是否成功（rowcount 对 ON CONFLICT 不可靠）
        if db.execute(stmt).first() is None:
            # 占位失败说明 key 已存在：返回首次结果，或校验请求体一致性
            existing = db.scalar(
                select(IdempotencyKey).where(
                    IdempotencyKey.user_id == user.id, IdempotencyKey.key == idempotency_key
                )
            )
            order = db.get(Order, existing.order_id) if existing else None
            if existing is None or order is None:
                raise BizException(ErrorCode.DUPLICATE_SUBMIT, "请求处理中，请稍后查看订单")
            if existing.request_hash != request_hash:
                raise BizException(ErrorCode.DUPLICATE_SUBMIT, "相同幂等键携带了不同的请求")
            return order

    # 1. 地址归属
    address = db.scalar(
        select(Address).where(Address.id == payload.address_id, Address.user_id == user.id)
    )
    if address is None:
        raise BizException(ErrorCode.NOT_FOUND, "收货地址不存在")

    # 2. 购物车项归属（他人 id 直接 404）
    items = db.scalars(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.id.in_(payload.cart_item_ids)
        )
    ).all()
    if len(items) != len(set(payload.cart_item_ids)):
        raise BizException(ErrorCode.NOT_FOUND, "部分购物车项不存在")

    # 3. 校验商品可售，并一次性缓存 SKU/商品（避免后续重复查询）
    sorted_items = sorted(items, key=lambda x: x.sku_id)
    sku_map: dict[int, Sku] = {}
    product_map: dict[int, Product] = {}
    for item in sorted_items:
        sku = db.get(Sku, item.sku_id)
        if sku is None or not sku.is_active:
            db.rollback()
            raise BizException(ErrorCode.STATE_UNAVAILABLE, "商品规格不存在或已停售")
        product = db.get(Product, sku.product_id)
        if product is None or not product.is_active:
            db.rollback()
            raise BizException(ErrorCode.STATE_UNAVAILABLE, "商品已下架")
        sku_map[sku.id] = sku
        product_map[sku.id] = product

    # 4. 按 sku_id 升序扣库存（条件更新，防超卖与死锁）
    for item in sorted_items:
        sku = sku_map[item.sku_id]
        result = _exec_update(
            db,
            update(Sku)
            .where(Sku.id == sku.id, Sku.stock >= item.quantity)
            .values(stock=Sku.stock - item.quantity),
        )
        if result.rowcount == 0:
            db.rollback()
            raise BizException(ErrorCode.STOCK_NOT_ENOUGH, f"库存不足：{sku.sku_code}")

    # 5. 生成订单与明细快照
    total = sum(sku_map[i.sku_id].price * i.quantity for i in sorted_items)
    order = Order(
        order_no="",  # 先占位，flush 拿到自增 id 后再生成唯一单号
        user_id=user.id,
        status="pending",
        total_amount=total,
        address_snapshot=_build_snapshot(address).model_dump(),
        remark=payload.remark,
    )
    db.add(order)
    db.flush()  # 让数据库分配 order.id
    order.order_no = _build_order_no(_now(), order.id)

    for item in sorted_items:
        sku = sku_map[item.sku_id]
        product = product_map[sku.id]
        db.add(
            OrderItem(
                order_id=order.id,
                sku_id=sku.id,
                product_id=product.id,
                product_name=product.name,
                sku_attrs=sku.attrs or {},
                main_image=product.main_image,
                price=sku.price,
                quantity=item.quantity,
            )
        )

    # 6. 清除购物车选中项
    for item in items:
        db.delete(item)

    # 7. 幂等键关联订单（占位已原子完成，此处补 order_id）
    if idempotency_key:
        db.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.user_id == user.id, IdempotencyKey.key == idempotency_key)
            .values(order_id=order.id)
        )

    db.commit()
    db.refresh(order)
    return order


# ---------- 状态流转 ----------

def _pay_sales_count(db: Session, order: Order) -> None:
    for item in order.items:
        db.execute(
            update(Product)
            .where(Product.id == item.product_id)
            .values(sales_count=Product.sales_count + item.quantity)
        )


def pay_order(db: Session, user: User, order_id: int) -> Order:
    order = _get_owned_order(db, user, order_id)
    result = _exec_update(db,
        update(Order)
        .where(Order.id == order.id, Order.status == "pending")
        .values(status="paid", paid_at=_now())
    )
    if result.rowcount == 0:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待支付订单可支付")
    db.refresh(order)
    _pay_sales_count(db, order)
    db.commit()
    db.refresh(order)
    return order


def _rollback_stock(db: Session, order: Order) -> None:
    """回滚订单占用的库存；SKU 已物理删除时记录告警（S-09）。"""
    for item in order.items:
        if item.sku_id:
            db.execute(
                update(Sku).where(Sku.id == item.sku_id).values(stock=Sku.stock + item.quantity)
            )
        else:
            logging.getLogger("xuanwu.error").warning(
                "rollback stock failed: sku deleted, order_id=%s item_id=%s", order.id, item.id
            )


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    order = _get_owned_order(db, user, order_id)
    result = _exec_update(db,
        update(Order)
        .where(Order.id == order.id, Order.status == "pending")
        .values(status="cancelled", cancelled_at=_now())
    )
    if result.rowcount == 0:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待支付订单可取消")
    db.refresh(order)
    # 回滚库存（与状态更新同一事务）
    _rollback_stock(db, order)
    db.commit()
    db.refresh(order)
    return order


def confirm_order(db: Session, user: User, order_id: int) -> Order:
    order = _get_owned_order(db, user, order_id)
    result = _exec_update(db,
        update(Order)
        .where(Order.id == order.id, Order.status == "shipped")
        .values(status="completed", completed_at=_now())
    )
    if result.rowcount == 0:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待收货订单可确认收货")
    db.commit()
    db.refresh(order)
    return order


# ---------- 查询 ----------

def list_orders(db: Session, user: User, status: str | None, page: int, size: int) -> tuple[list[OrderListItem], int]:
    query = select(Order).where(Order.user_id == user.id)
    if status and status != "all":
        query = query.where(Order.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    orders = db.scalars(
        query.order_by(Order.created_at.desc(), Order.id.desc()).offset((page - 1) * size).limit(size)
    ).all()

    items = []
    for order in orders:
        first = order.items[0] if order.items else None
        items.append(
            OrderListItem(
                id=order.id,
                order_no=order.order_no,
                status=order.status,
                total_amount=format_price(order.total_amount),
                created_at=order.created_at,
                total_quantity=sum(i.quantity for i in order.items),
                preview_image=first.main_image if first else None,
                preview_name=first.product_name if first else None,
            )
        )
    return items, total


def get_order_detail(db: Session, user: User, order_id: int) -> OrderDetail:
    order = _get_owned_order(db, user, order_id)
    return OrderDetail(
        id=order.id,
        order_no=order.order_no,
        status=order.status,
        total_amount=format_price(order.total_amount),
        remark=order.remark,
        created_at=order.created_at,
        address_snapshot=AddressSnapshot(**order.address_snapshot),
        items=[_to_item_out(i) for i in order.items],
        timeline=_build_timeline(order),
    )


# ---------- 管理端 ----------

def admin_ship_order(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise BizException(ErrorCode.NOT_FOUND)
    result = _exec_update(db,
        update(Order)
        .where(Order.id == order.id, Order.status == "paid")
        .values(status="shipped", shipped_at=_now())
    )
    if result.rowcount == 0:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待发货订单可发货")
    db.commit()
    db.refresh(order)
    return order


def admin_list_orders(
    db: Session,
    order_no: str | None,
    status: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    page: int,
    size: int,
) -> tuple[list[OrderListItem], int]:
    query = select(Order)
    if order_no:
        query = query.where(Order.order_no == order_no.strip())
    valid_statuses = {"pending", "paid", "shipped", "completed", "cancelled"}
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        invalid = [s for s in statuses if s not in valid_statuses]
        if invalid:
            raise BizException(ErrorCode.PARAM_INVALID, "订单状态值非法")
        if statuses:
            query = query.where(Order.status.in_(statuses))
    if start_time and end_time and start_time > end_time:
        raise BizException(ErrorCode.PARAM_CONFLICT, "开始时间不能晚于结束时间")
    if start_time:
        query = query.where(Order.created_at >= start_time)
    if end_time:
        query = query.where(Order.created_at <= end_time)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    orders = db.scalars(
        query.order_by(Order.created_at.desc(), Order.id.desc()).offset((page - 1) * size).limit(size)
    ).all()

    # 一次查出当前页所有订单的用户，避免 N+1
    user_map: dict[int, User] = {}
    if orders:
        users = db.scalars(select(User).where(User.id.in_([o.user_id for o in orders]))).all()
        user_map = {u.id: u for u in users}

    items = []
    for order in orders:
        first = order.items[0] if order.items else None
        user = user_map.get(order.user_id)
        snapshot = order.address_snapshot or {}
        items.append(
            AdminOrderListItem(
                id=order.id,
                order_no=order.order_no,
                status=order.status,
                total_amount=format_price(order.total_amount),
                created_at=order.created_at,
                total_quantity=sum(i.quantity for i in order.items),
                preview_image=first.main_image if first else None,
                preview_name=first.product_name if first else None,
                receiver=snapshot.get("receiver"),
                phone=snapshot.get("phone"),
                user_email=user.email if user else None,
            )
        )
    return items, total


# ---------- 超时任务 ----------

def force_expire_order(db: Session, order_id: int) -> Order:
    """测试钩子：立即把指定待支付订单置为已取消并回滚库存，不依赖 30 分钟超时。"""
    order = db.get(Order, order_id)
    if order is None:
        raise BizException(ErrorCode.NOT_FOUND)
    result = _exec_update(db,
        update(Order)
        .where(Order.id == order_id, Order.status == "pending")
        .values(status="cancelled", cancelled_at=_now())
    )
    if result.rowcount == 0:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "仅待支付订单可触发超时取消")
    db.refresh(order)
    _rollback_stock(db, order)
    db.commit()
    db.refresh(order)
    return order


def expire_pending_orders(db: Session) -> int:
    """取消超时未支付订单并回滚库存。每单独立事务，单笔失败不中断整批。返回成功数。"""
    logger = logging.getLogger("xuanwu.scheduler")
    cutoff = _now() - timedelta(minutes=settings.order_expire_minutes)
    order_ids = db.scalars(
        select(Order.id).where(Order.status == "pending", Order.created_at < cutoff).limit(500)
    ).all()
    count = 0
    for order_id in order_ids:
        try:
            result = _exec_update(db,
                update(Order)
                .where(Order.id == order_id, Order.status == "pending")
                .values(status="cancelled", cancelled_at=_now())
            )
            if result.rowcount == 0:
                db.commit()
                continue
            order = db.get(Order, order_id)
            if order is None:
                continue
            _rollback_stock(db, order)
            db.commit()
            count += 1
        except Exception:
            db.rollback()
            logger.exception("expire order %s failed", order_id)
    logger.info("expire_pending scanned=%s succeeded=%s", len(order_ids), count)
    return count


def auto_confirm_shipped_orders(db: Session) -> int:
    """超时自动确认收货。每单独立事务，单笔失败不中断整批。返回成功数。"""
    logger = logging.getLogger("xuanwu.scheduler")
    cutoff = _now() - timedelta(days=settings.order_auto_confirm_days)
    order_ids = db.scalars(
        select(Order.id).where(Order.status == "shipped", Order.shipped_at < cutoff).limit(500)
    ).all()
    count = 0
    for order_id in order_ids:
        try:
            result = _exec_update(db,
                update(Order)
                .where(Order.id == order_id, Order.status == "shipped")
                .values(status="completed", completed_at=_now())
            )
            db.commit()
            if result.rowcount:
                count += 1
        except Exception:
            db.rollback()
            logger.exception("auto_confirm order %s failed", order_id)
    logger.info("auto_confirm scanned=%s succeeded=%s", len(order_ids), count)
    return count
