"""商品与 SKU 业务（需求 FR-U-03/04、FR-A-01）。"""
import logging
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.core.money import escape_like, format_price
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sku import Sku
from app.schemas.product import (
    PriceRange,
    ProductAdminItem,
    ProductCreate,
    ProductDetail,
    ProductListItem,
    ProductUpdate,
    SkuIn,
    SkuOut,
)
from app.services import category_service


def _parse_price(value: str | None) -> Decimal | None:
    """解析并校验价格参数，非数字或负数返回 400（E-07）。"""
    if value is None or value.strip() == "":
        return None
    try:
        amount = Decimal(value.strip())
    except (InvalidOperation, ValueError):
        raise BizException(ErrorCode.PARAM_INVALID, "价格格式不正确") from None
    if amount < 0:
        raise BizException(ErrorCode.PARAM_INVALID, "价格不能为负数")
    return amount


def build_attrs_key(attrs: dict[str, str]) -> str:
    return "|".join(f"{k}:{attrs[k]}" for k in sorted(attrs))


def _spec_keys(skus: Sequence[Sku]) -> list[str]:
    keys: list[str] = []
    for sku in skus:
        for key in (sku.attrs or {}):
            if key not in keys:
                keys.append(key)
    return keys


def _to_sku_out(sku: Sku) -> SkuOut:
    return SkuOut(
        id=sku.id,
        sku_code=sku.sku_code,
        attrs=sku.attrs,
        price=format_price(sku.price),
        stock=sku.stock,
        is_active=sku.is_active,
    )


def _get_or_404(db: Session, product_id: int, *, include_inactive: bool = False) -> Product:
    product = db.get(Product, product_id)
    if product is None or (not include_inactive and not product.is_active):
        raise BizException(ErrorCode.NOT_FOUND, "商品不存在或已下架")
    return product


# ---------- 用户端 ----------

def list_products(
    db: Session,
    category_id: int | None,
    keyword: str | None,
    min_price: str | None,
    max_price: str | None,
    sort: str,
    page: int,
    size: int,
) -> tuple[list[ProductListItem], int]:
    min_price_sq = (
        select(
            Sku.product_id,
            func.min(Sku.price).label("min_price"),
            func.max(Sku.price).label("max_price"),
        )
        .where(Sku.is_active.is_(True), Sku.stock > 0)
        .group_by(Sku.product_id)
        .subquery()
    )
    stock_sq = (
        select(Sku.product_id, func.coalesce(func.sum(Sku.stock), 0).label("total_stock"))
        .group_by(Sku.product_id)
        .subquery()
    )

    query = (
        select(
            Product,
            min_price_sq.c.min_price,
            min_price_sq.c.max_price,
            stock_sq.c.total_stock,
        )
        .outerjoin(min_price_sq, min_price_sq.c.product_id == Product.id)
        .outerjoin(stock_sq, stock_sq.c.product_id == Product.id)
        .where(Product.is_active.is_(True))
    )

    # BR-17：仅展示至少一个「在售且有库存」SKU 的商品
    has_sellable_sku = exists().where(
        Sku.product_id == Product.id, Sku.is_active.is_(True), Sku.stock > 0
    )
    query = query.where(has_sellable_sku)

    if category_id is not None:
        ids = category_service.get_descendant_ids(db, category_id)
        query = query.where(Product.category_id.in_(ids))

    if keyword:
        kw = escape_like(keyword.strip())
        if kw:
            query = query.where(Product.name.ilike(f"%{kw}%", escape="\\"))

    if min_price is not None or max_price is not None:
        min_dec = _parse_price(min_price)
        max_dec = _parse_price(max_price)
        if min_dec is not None and max_dec is not None and min_dec > max_dec:
            raise BizException(ErrorCode.PARAM_CONFLICT, "最低价不能大于最高价")
        if min_dec is not None:
            query = query.where(min_price_sq.c.min_price >= min_dec)
        if max_dec is not None:
            query = query.where(min_price_sq.c.min_price <= max_dec)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    if sort == "price_asc":
        query = query.order_by(min_price_sq.c.min_price.asc(), Product.id.desc())
    elif sort == "price_desc":
        query = query.order_by(min_price_sq.c.min_price.desc(), Product.id.desc())
    else:  # default / sales_desc
        query = query.order_by(Product.sales_count.desc(), Product.id.desc())

    rows = db.execute(query.offset((page - 1) * size).limit(size)).all()
    items = []
    for product, min_p, max_p, total_stock in rows:
        items.append(
            ProductListItem(
                id=product.id,
                name=product.name,
                main_image=product.main_image,
                category_id=product.category_id,
                price=format_price(min_p if min_p is not None else Decimal("0")),
                max_price=format_price(max_p if max_p is not None else Decimal("0")),
                sales_count=product.sales_count,
                has_stock=(total_stock or 0) > 0,
            )
        )
    return items, total


def get_product_detail(db: Session, product_id: int) -> ProductDetail:
    product = _get_or_404(db, product_id)
    skus = db.scalars(select(Sku).where(Sku.product_id == product_id).order_by(Sku.id)).all()
    if not skus:
        # 数据异常：商品无任何 SKU（N-06），记录告警便于定位
        logging.getLogger("xuanwu.error").warning("product %s has no SKU", product_id)
        raise BizException(ErrorCode.NOT_FOUND, "商品暂无可用规格")

    active_prices = [s.price for s in skus if s.is_active]
    price_min = min(active_prices) if active_prices else Decimal("0")
    price_max = max(active_prices) if active_prices else Decimal("0")

    return ProductDetail(
        id=product.id,
        name=product.name,
        description=product.description,
        main_image=product.main_image,
        images=product.images or [],
        category_id=product.category_id,
        sales_count=product.sales_count,
        price_range=PriceRange(min=format_price(price_min), max=format_price(price_max)),
        spec_keys=_spec_keys(skus),
        skus=[_to_sku_out(s) for s in skus],
    )


# ---------- 管理端 ----------

def _validate_skus(payload: ProductCreate | ProductUpdate) -> None:
    if not payload.skus:
        raise BizException(ErrorCode.PARAM_INVALID, "至少需要一个 SKU")
    first_keys = set(payload.skus[0].attrs.keys())
    for sku in payload.skus:
        if set(sku.attrs.keys()) != first_keys:
            raise BizException(ErrorCode.PARAM_INVALID, "同一商品下所有 SKU 的规格键集合必须一致")
    seen: set[str] = set()
    for sku in payload.skus:
        key = build_attrs_key(sku.attrs)
        if key in seen:
            raise BizException(ErrorCode.ALREADY_EXISTS, "SKU 规格组合重复")
        seen.add(key)


def _check_sku_code_conflict(
    db: Session, sku_codes: list[str], exclude_product_id: int | None = None
) -> None:
    """SKU 编码全局唯一预检。

    编辑场景必须传 exclude_product_id：不改编码的旧 SKU 会被自己的编码误判为冲突。
    同时拦截同一份提交内部重复的编码，否则只能落到数据库唯一约束的笼统 409。
    """
    seen: set[str] = set()
    for code in sku_codes:
        if code in seen:
            raise BizException(ErrorCode.PARAM_INVALID, f"SKU 编码重复：{code}")
        seen.add(code)

        stmt = select(Sku.id).where(Sku.sku_code == code)
        if exclude_product_id is not None:
            stmt = stmt.where(Sku.product_id != exclude_product_id)
        if db.scalar(stmt.limit(1)):
            raise BizException(ErrorCode.ALREADY_EXISTS, f"SKU 编码已存在：{code}")


def _sync_skus(db: Session, product: Product, skus: list[SkuIn]) -> None:
    """差量同步 SKU：按 attrs_key 对齐，原地更新 / 新增 / 下线，不做删光重建。

    为什么不能"删光重建"（审查报告 C1）：skus 同时是 cart_items 与 order_items 的父表，
    - cart_items.sku_id 为 ON DELETE CASCADE → 会静默清空所有用户的购物车条目；
    - order_items.sku_id 为 ON DELETE SET NULL → 历史订单失去 sku_id，
      _rollback_stock 的 `if item.sku_id` 判断会跳过它，库存永久不回滚。
    因此被订单引用的 SKU 只做软删除（is_active=False），保住主键。
    """
    existing = {
        sku.attrs_key: sku
        for sku in db.scalars(select(Sku).where(Sku.product_id == product.id)).all()
    }

    incoming: set[str] = set()
    for item in skus:
        attrs_key = build_attrs_key(item.attrs)
        incoming.add(attrs_key)
        current = existing.get(attrs_key)
        if current is None:
            db.add(
                Sku(
                    product_id=product.id,
                    sku_code=item.sku_code,
                    attrs=item.attrs,
                    attrs_key=attrs_key,
                    price=item.price,
                    stock=item.stock,
                    is_active=item.is_active,
                )
            )
            continue
        current.sku_code = item.sku_code
        current.attrs = item.attrs
        current.price = item.price
        current.stock = item.stock
        current.is_active = item.is_active

    for attrs_key, current in existing.items():
        if attrs_key in incoming:
            continue
        referenced = db.scalar(select(OrderItem.id).where(OrderItem.sku_id == current.id).limit(1))
        if referenced:
            # 有历史订单引用：软删除，保留 sku_id，让库存回滚与订单展示继续可用
            current.is_active = False
        else:
            db.delete(current)

    db.flush()


def create_product(db: Session, payload: ProductCreate, merchant_id: int | None = None) -> Product:
    _validate_skus(payload)
    _check_sku_code_conflict(db, [s.sku_code for s in payload.skus])
    # 分类存在性校验
    category_service.get_or_404(db, payload.category_id)

    product = Product(
        name=payload.name,
        category_id=payload.category_id,
        merchant_id=merchant_id,
        description=payload.description,
        main_image=payload.main_image,
        images=payload.images,
        is_active=payload.is_active,
    )
    db.add(product)
    db.flush()
    _sync_skus(db, product, payload.skus)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = _get_or_404(db, product_id, include_inactive=True)
    _validate_skus(payload)
    # 编辑时排除本商品自有 SKU 的编码，否则未改动的编码会被自己判为冲突
    _check_sku_code_conflict(
        db, [s.sku_code for s in payload.skus], exclude_product_id=product_id
    )
    category_service.get_or_404(db, payload.category_id)

    product.name = payload.name
    product.category_id = payload.category_id
    product.description = payload.description
    product.main_image = payload.main_image
    product.images = payload.images
    product.is_active = payload.is_active
    _sync_skus(db, product, payload.skus)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = _get_or_404(db, product_id, include_inactive=True)
    # 用 order_items.product_id 判断：它是下单时固化的快照字段，不会因 SKU 变更被置空。
    # 原先 JOIN Sku ON sku_id 的写法在 SKU 被重建后 join 不到，守卫会失效。
    has_orders = db.scalar(
        select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)
    )
    if has_orders:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "该商品存在历史订单，请改为下架")
    db.delete(product)
    db.commit()


def set_product_status(db: Session, product_id: int, is_active: bool) -> Product:
    product = _get_or_404(db, product_id, include_inactive=True)
    product.is_active = is_active
    db.commit()
    db.refresh(product)
    return product


def admin_list_products(
    db: Session,
    keyword: str | None,
    category_id: int | None,
    is_active: bool | None,
    page: int,
    size: int,
) -> tuple[list[ProductAdminItem], int]:
    query = select(Product)
    if keyword:
        kw = escape_like(keyword.strip())
        if kw:
            query = query.where(Product.name.ilike(f"%{kw}%", escape="\\"))
    if category_id is not None:
        query = query.where(Product.category_id.in_(category_service.get_descendant_ids(db, category_id)))
    if is_active is not None:
        query = query.where(Product.is_active.is_(is_active))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    products = db.scalars(
        query.order_by(Product.id.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return build_admin_items(db, products), total


def build_admin_items(db: Session, products: Sequence[Product]) -> list[ProductAdminItem]:
    """把商品列表构造成管理端条目（含 SKU），批量查 SKU 避免 N+1。"""
    sku_map: dict[int, list[Sku]] = {}
    if products:
        skus = db.scalars(
            select(Sku).where(Sku.product_id.in_([p.id for p in products])).order_by(Sku.id)
        ).all()
        for s in skus:
            sku_map.setdefault(s.product_id, []).append(s)

    items = []
    for p in products:
        skus = sku_map.get(p.id, [])
        prices = [s.price for s in skus]
        total_stock = sum(s.stock for s in skus)
        items.append(
            ProductAdminItem(
                id=p.id,
                name=p.name,
                main_image=p.main_image,
                category_id=p.category_id,
                description=p.description,
                price=format_price(min(prices)) if prices else "0.00",
                max_price=format_price(max(prices)) if prices else "0.00",
                sales_count=p.sales_count,
                has_stock=total_stock > 0,
                is_active=p.is_active,
                sku_count=len(skus),
                skus=[_to_sku_out(s) for s in skus],
            )
        )
    return items


def get_product_admin(db: Session, product_id: int) -> ProductAdminItem:
    product = _get_or_404(db, product_id, include_inactive=True)
    skus = db.scalars(select(Sku).where(Sku.product_id == product_id).order_by(Sku.id)).all()
    prices = [s.price for s in skus]
    return ProductAdminItem(
        id=product.id,
        name=product.name,
        main_image=product.main_image,
        category_id=product.category_id,
        description=product.description,
        price=format_price(min(prices)) if prices else "0.00",
        max_price=format_price(max(prices)) if prices else "0.00",
        sales_count=product.sales_count,
        has_stock=sum(s.stock for s in skus) > 0,
        is_active=product.is_active,
        sku_count=len(skus),
        skus=[_to_sku_out(s) for s in skus],
    )
