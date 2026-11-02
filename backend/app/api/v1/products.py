from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import PageData, success
from app.database import get_db
from app.services import product_service

router = APIRouter(prefix="/products", tags=["商品"])

SortKey = Literal["default", "sales_desc", "price_asc", "price_desc"]


@router.get("", summary="商品列表（筛选/搜索/排序/分页）")
def list_products(
    category_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=50),
    min_price: str | None = Query(default=None),
    max_price: str | None = Query(default=None),
    sort: SortKey = Query(default="default"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = product_service.list_products(
        db, category_id, keyword, min_price, max_price, sort, page, size
    )
    return success(PageData.build(items, total, page, size))


@router.get("/{product_id}", summary="商品详情")
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    return success(product_service.get_product_detail(db, product_id))
