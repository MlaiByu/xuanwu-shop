import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


class AddressBase(BaseModel):
    receiver: str = Field(min_length=1, max_length=20)
    phone: str = Field(min_length=1, max_length=20)
    province: str = Field(min_length=1, max_length=50)
    city: str = Field(min_length=1, max_length=50)
    district: str = Field(min_length=1, max_length=50)
    detail: str = Field(min_length=5, max_length=200)
    is_default: bool = False

    @field_validator("receiver", "phone", "province", "city", "district", "detail", mode="before")
    @classmethod
    def strip_text(cls, value):
        # 先 strip 再走 Field 约束，避免纯空白字符串通过 min_length 校验
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not PHONE_PATTERN.fullmatch(value):
            raise ValueError("手机号格式不正确")
        return value


class AddressCreate(AddressBase):
    pass


class AddressUpdate(AddressBase):
    pass


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: bool
