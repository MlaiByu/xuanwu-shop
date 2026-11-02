from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.money import format_price


class SkuIn(BaseModel):
    sku_code: str = Field(min_length=1, max_length=64)
    attrs: dict[str, str]
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0, default=0)
    is_active: bool = True

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        # 拒绝超过两位小数（E-32），不做静默四舍五入
        if value != value.quantize(Decimal("0.01")):
            raise ValueError("价格最多保留两位小数")
        return value

    @field_validator("attrs")
    @classmethod
    def validate_attrs(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("SKU 规格属性不能为空")
        for key, val in value.items():
            if not key.strip() or not str(val).strip():
                raise ValueError("规格属性键与值均不能为空")
        return value


class SkuOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    attrs: dict
    price: str
    stock: int
    is_active: bool

    @model_validator(mode="before")
    @classmethod
    def convert_price(cls, data):
        price = getattr(data, "price", None)
        if price is not None:
            return {
                "id": data.id,
                "sku_code": data.sku_code,
                "attrs": data.attrs,
                "price": format_price(price),
                "stock": data.stock,
                "is_active": data.is_active,
            }
        return data


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category_id: int
    description: str | None = None
    main_image: str = Field(min_length=1, max_length=500)
    images: list[str] = Field(default_factory=list)
    is_active: bool = True


class ProductCreate(ProductBase):
    skus: list[SkuIn] = Field(min_length=1)


class ProductUpdate(ProductBase):
    skus: list[SkuIn] = Field(min_length=1)


class ProductStatusIn(BaseModel):
    """上下架请求体。

    不能用裸 dict 接收：`bool("false") == True`，字符串 "false" 会被当成上架。
    """

    is_active: bool = True


class ProductListItem(BaseModel):
    id: int
    name: str
    main_image: str
    category_id: int
    price: str
    max_price: str
    sales_count: int
    has_stock: bool
    is_active: bool | None = None
    sku_count: int | None = None


class PriceRange(BaseModel):
    min: str
    max: str


class ProductDetail(BaseModel):
    id: int
    name: str
    description: str | None
    main_image: str
    images: list
    category_id: int
    sales_count: int
    price_range: PriceRange
    spec_keys: list[str]
    skus: list[SkuOut]


class ProductAdminItem(ProductListItem):
    description: str | None = None
    skus: list[SkuOut] = Field(default_factory=list)
