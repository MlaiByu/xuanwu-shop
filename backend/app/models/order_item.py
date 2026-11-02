from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JSONType

if TYPE_CHECKING:
    from app.models.order import Order


class OrderItem(Base):
    """订单明细。

    名称、属性、价格、主图均为下单时快照，此后不随商品修改而变化。
    sku_id 允许为空且 ON DELETE SET NULL：商品被物理删除后历史订单仍可展示。
    """

    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_items_quantity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku_id: Mapped[int | None] = mapped_column(
        ForeignKey("skus.id", ondelete="SET NULL"), nullable=True
    )
    # 不做外键约束，仅作溯源字段：商品可被物理删除，订单不允许被牵连（§8.9）
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 商家归属快照（下单时固化），商家据此查询自己的订单
    merchant_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku_attrs: Mapped[dict] = mapped_column(JSONType, nullable=False)
    main_image: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
