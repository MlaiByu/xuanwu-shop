from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.responses import PageData, success
from app.database import get_db
from app.schemas.product import ProductCreate, ProductStatusIn, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["管理端-商品"], dependencies=[Depends(get_current_admin)])


@router.get("", summary="商品列表")
def admin_list_products(
    keyword: str | None = Query(default=None, max_length=50),
    category_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = product_service.admin_list_products(db, keyword, category_id, is_active, page, size)
    return success(PageData.build(items, total, page, size))


@router.post("", summary="新增商品")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return success(product_service.create_product(db, payload))


@router.get("/{product_id}", summary="商品详情")
def admin_get_product(product_id: int, db: Session = Depends(get_db)):
    return success(product_service.get_product_admin(db, product_id))


@router.put("/{product_id}", summary="编辑商品")
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    return success(product_service.update_product(db, product_id, payload))


@router.delete("/{product_id}", summary="删除商品")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product_service.delete_product(db, product_id)
    return success()


@router.patch("/{product_id}/status", summary="上下架")
def set_product_status(
    product_id: int,
    payload: ProductStatusIn,
    db: Session = Depends(get_db),
):
    return success(product_service.set_product_status(db, product_id, payload.is_active))
