from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class OrderCreate(BaseModel):
    address_id: int
    cart_item_ids: list[int] = Field(min_length=1)
    remark: str | None = Field(default=None, max_length=200)


class OrderItemOut(BaseModel):
    id: int
    product_name: str
    sku_attrs: dict
    main_image: str
    price: str
    quantity: int
    subtotal: str


class AddressSnapshot(BaseModel):
    receiver: str
    phone: str
    province: str
    city: str
    district: str
    detail: str


class OrderListItem(BaseModel):
    id: int
    order_no: str
    status: str
    total_amount: str
    created_at: datetime
    total_quantity: int
    preview_image: str | None = None
    preview_name: str | None = None


class TimelineEvent(BaseModel):
    label: str
    time: datetime

    @field_serializer("time")
    def serialize_time(self, value: datetime) -> str:
        return value.isoformat()


class OrderDetail(BaseModel):
    id: int
    order_no: str
    status: str
    total_amount: str
    remark: str | None
    created_at: datetime
    address_snapshot: AddressSnapshot
    items: list[OrderItemOut]
    timeline: list[TimelineEvent]

    @field_serializer("created_at")
    def serialize_created(self, value: datetime) -> str:
        return value.isoformat()


class CheckoutItem(BaseModel):
    cart_item_id: int
    product_name: str
    sku_attrs: dict
    main_image: str
    price: str
    quantity: int
    subtotal: str
    is_valid: bool


class CheckoutPreview(BaseModel):
    address: dict | None
    items: list[CheckoutItem]
    total_quantity: int
    total_amount: str
    freight: str = "0.00"


class AdminOrderListItem(OrderListItem):
    receiver: str | None = None
    phone: str | None = None
    user_email: str | None = None
