from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONType, TimestampMixin


class Sku(TimestampMixin, Base):
    __tablename__ = "skus"
    __table_args__ = (
        # 数据库层兜底：即使应用层写错，也不允许出现负库存（需求 §7.4）
        CheckConstraint("stock >= 0", name="ck_skus_stock_non_negative"),
        CheckConstraint("price >= 0", name="ck_skus_price_non_negative"),
        UniqueConstraint("product_id", "attrs_key", name="uq_skus_product_attrs"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    attrs: Mapped[dict] = mapped_column(JSONType, nullable=False)
    # 规范化属性串（键按字典序拼接），用于唯一约束；JSONB 本身无法直接建唯一索引
    attrs_key: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
