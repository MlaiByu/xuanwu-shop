from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONType, TimestampMixin


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category_active", "category_id", "is_active"),
        Index("ix_products_active_sales", "is_active", "sales_count", "id"),
        # pg_trgm 模糊搜索索引（仅 PostgreSQL；定义进模型避免 autogenerate 误删）
        Index(
            "idx_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    # 归属商家；NULL 表示平台自营（ABC 三端 B 端）
    merchant_id: Mapped[int | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_image: Mapped[str] = mapped_column(String(500), nullable=False)
    images: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 销量冗余字段，避免列表页排序时实时聚合订单表
    sales_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
