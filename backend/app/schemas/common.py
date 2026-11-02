from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """统一分页参数（需求 §2.3）。

    page 从 1 开始；size 上限 100，超出由 Pydantic 直接返回 400。
    """

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
