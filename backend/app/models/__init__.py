"""统一导出所有模型，供 Alembic 自动发现元数据。"""
from app.models.address import Address
from app.models.base import Base
from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.idempotency_key import IdempotencyKey
from app.models.merchant import Merchant
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sku import Sku
from app.models.support_ticket import SupportTicket
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Category",
    "Merchant",
    "Product",
    "Sku",
    "CartItem",
    "Address",
    "Order",
    "OrderItem",
    "IdempotencyKey",
    "SupportTicket",
]
