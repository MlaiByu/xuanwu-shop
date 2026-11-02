"""客服可调用的“工具”。

三条硬约束：
1. 订单类查询**必须**同时匹配 user_id —— 用户只能查自己的单，单号猜对了也不行。
2. 工具只读，不下单、不退款、不改地址；涉及资金与履约的动作一律转人工。
3. 返回值是结构化事实（dict），交给生成节点做措辞，避免模型自由发挥。
"""

import re
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
from app.models.sku import Sku

ORDER_NO_PATTERN = re.compile(r"\d{16,24}")

STATUS_TEXT = {
    "pending": "待支付",
    "paid": "已付款，待发货",
    "shipped": "已发货",
    "completed": "已完成",
    "cancelled": "已取消",
}

STATUS_HINT = {
    "pending": "15 分钟内未支付会自动关闭，库存也会释放。",
    "paid": "仓库正在打包，48 小时内发出。",
    "shipped": "已交给顺丰，正常情况下 2-3 天送达。",
    "completed": "已签收完成。7 天内如有问题可以申请售后。",
    "cancelled": "订单已取消，库存已释放，想买可以重新下单。",
}


def extract_order_no(text: str) -> str | None:
    """从用户输入里提取订单号（16-24 位纯数字）。"""
    match = ORDER_NO_PATTERN.search(text or "")
    return match.group(0) if match else None


def _order_brief(order: Order) -> dict[str, Any]:
    items = order.items or []
    first = items[0].product_name if items else "商品"
    quantity = sum(item.quantity for item in items)
    return {
        "order_no": order.order_no,
        "status": order.status,
        "status_text": STATUS_TEXT.get(order.status, order.status),
        "total_amount": str(order.total_amount),
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "",
        "item_summary": f"{first} 等 {quantity} 件" if len(items) > 1 else f"{first} × {quantity}",
        "quantity": quantity,
    }


def recent_orders(db: Session, user_id: int | None, limit: int = 3) -> dict[str, Any]:
    if not user_id:
        return {
            "ok": False,
            "type": "order",
            "reason": "anonymous",
            "message": "用户未登录，无法查询订单",
        }
    rows = db.scalars(
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    ).all()
    if not rows:
        return {
            "ok": False,
            "type": "order",
            "reason": "empty",
            "message": "该用户没有任何订单",
        }
    return {
        "ok": True,
        "type": "order",
        "data": {"orders": [_order_brief(order) for order in rows]},
    }


def order_detail(
    db: Session, user_id: int | None, order_no: str | None = None
) -> dict[str, Any]:
    """按单号查订单；未给单号时退化为最近一单。"""
    if not user_id:
        return {
            "ok": False,
            "type": "order",
            "reason": "anonymous",
            "message": "用户未登录，无法查询订单",
        }

    order: Order | None
    if order_no:
        # user_id 与 order_no 同时匹配：越权查询在这里被挡住
        order = db.scalar(
            select(Order).where(Order.order_no == order_no, Order.user_id == user_id)
        )
        if order is None:
            return {
                "ok": False,
                "type": "order",
                "reason": "not_found",
                "message": f"没有找到单号 {order_no} 的订单（也可能不属于当前账号）",
            }
    else:
        order = db.scalar(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        if order is None:
            return {
                "ok": False,
                "type": "order",
                "reason": "empty",
                "message": "该用户没有任何订单",
            }

    items = [
        {
            "name": item.product_name,
            "attrs": " / ".join((item.sku_attrs or {}).values()),
            "price": str(item.price),
            "quantity": item.quantity,
        }
        for item in (order.items or [])
    ]
    address = order.address_snapshot or {}
    return {
        "ok": True,
        "type": "order",
        "data": {
            **_order_brief(order),
            "items": items,
            "receiver": address.get("receiver"),
            "address": f"{address.get('province', '')}{address.get('city', '')}"
            f"{address.get('district', '')}{address.get('detail', '')}",
            "remark": order.remark,
            "hint": STATUS_HINT.get(order.status, ""),
        },
    }


def logistics_status(
    db: Session, user_id: int | None, order_no: str | None = None
) -> dict[str, Any]:
    """物流进度。

    项目没有接快递公司接口，这里按订单状态与发货时间给出可解释的推断，
    不编造“已到达 XX 中转场”这类假轨迹。
    """
    result = order_detail(db, user_id, order_no)
    if not result["ok"]:
        return result

    data = result["data"]
    order = db.scalar(
        select(Order).where(
            Order.order_no == data["order_no"], Order.user_id == user_id
        )
    )
    expected = ""
    if order and order.status == "shipped" and order.shipped_at:
        expected = (order.shipped_at + timedelta(days=3)).strftime("%m月%d日")
    return {
        "ok": True,
        "type": "logistics",
        "data": {
            "order_no": data["order_no"],
            "status": data["status"],
            "status_text": data["status_text"],
            "shipped_at": order.shipped_at.strftime("%Y-%m-%d %H:%M")
            if order and order.shipped_at
            else None,
            "expected_arrival": expected,
            "hint": STATUS_HINT.get(data["status"], ""),
            "tracking_available": bool(order and order.status in ("shipped", "completed")),
        },
    }


def search_products(db: Session, keyword: str, limit: int = 3) -> dict[str, Any]:
    """按名称模糊查商品，返回最低价与总库存。"""
    word = (keyword or "").strip()
    if not word:
        return {"ok": False, "type": "product", "reason": "empty_keyword", "message": "没有可检索的关键词"}

    rows = db.scalars(
        select(Product)
        .where(Product.is_active.is_(True), Product.name.ilike(f"%{word}%"))
        .limit(limit)
    ).all()
    if not rows:
        return {
            "ok": False,
            "type": "product",
            "reason": "empty",
            "message": f"没有搜到和「{word}」相关的在售商品",
        }

    ids = [product.id for product in rows]
    stats = db.execute(
        select(
            Sku.product_id,
            func.min(Sku.price).label("min_price"),
            func.sum(Sku.stock).label("stock"),
        )
        .where(Sku.product_id.in_(ids), Sku.is_active.is_(True))
        .group_by(Sku.product_id)
    ).all()
    by_id = {row.product_id: row for row in stats}

    data = []
    for product in rows:
        stat = by_id.get(product.id)
        data.append(
            {
                "id": product.id,
                "name": product.name,
                "price": str(stat.min_price) if stat and stat.min_price is not None else None,
                "stock": int(stat.stock or 0) if stat else 0,
                "sales": product.sales_count,
            }
        )
    return {"ok": True, "type": "product", "data": {"products": data}}
