from pydantic import BaseModel, Field


class CartAdd(BaseModel):
    sku_id: int
    quantity: int = Field(ge=1, le=999)


class CartUpdate(BaseModel):
    quantity: int = Field(ge=1, le=999)


class CartItemOut(BaseModel):
    id: int
    sku_id: int
    product_id: int
    product_name: str
    main_image: str
    attrs: dict
    price: str
    quantity: int
    stock: int
    is_valid: bool
    subtotal: str


class CartSummary(BaseModel):
    items: list[CartItemOut]
    total_quantity: int
    total_amount: str
