"""统一响应体与分页结构（需求 §2.1、§2.3）。"""
import math
from typing import Any, Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageData(BaseModel, Generic[T]):
    """分页响应。total 为 0 时 pages 必须为 0，不是 1。"""

    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0

    @classmethod
    def build(cls, items: list[T], total: int, page: int, size: int) -> "PageData[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def error_response(code: int, http_status: int, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"code": code, "message": message, "data": data},
    )
