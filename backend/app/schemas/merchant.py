from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class MerchantApplyRequest(BaseModel):
    shop_name: str = Field(min_length=2, max_length=50)


class MerchantRejectRequest(BaseModel):
    remark: str = Field(min_length=1, max_length=200)


class MerchantOut(BaseModel):
    id: int
    user_id: int
    shop_name: str
    status: str
    audit_remark: str | None = None
    user_email: str | None = None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()
