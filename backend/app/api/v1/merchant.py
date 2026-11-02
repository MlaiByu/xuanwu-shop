"""商家端接口（ABC 三端 B 端）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_current_user
from app.core.responses import PageData, success
from app.database import get_db
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.merchant import MerchantApplyRequest, MerchantOut
from app.schemas.product import ProductCreate, ProductStatusIn, ProductUpdate
from app.services import merchant_service

router = APIRouter(prefix="/merchant", tags=["商家"])


@router.post("/apply", summary="申请入驻")
def apply_merchant(
    payload: MerchantApplyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant = merchant_service.apply(db, user, payload.shop_name)
    return success(
        MerchantOut(
            id=merchant.id,
            user_id=merchant.user_id,
            shop_name=merchant.shop_name,
            status=merchant.status,
            audit_remark=merchant.audit_remark,
            created_at=merchant.created_at,
        )
    )


@router.get("/profile", summary="店铺信息")
def get_profile(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    return success(merchant_service.get_profile(db, merchant))


@router.get("/products", summary="我的商品")
def list_products(merchant: Merchant = Depends(get_current_merchant), db: Session = Depends(get_db)):
    return success(merchant_service.list_products(db, merchant))


@router.post("/products", summary="创建商品")
def create_product(
    payload: ProductCreate,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    product = merchant_service.create_product(db, merchant, payload)
    return success({"id": product.id, "name": product.name})


@router.put("/products/{product_id}", summary="编辑商品")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    product = merchant_service.update_product(db, merchant, product_id, payload)
    return success({"id": product.id, "name": product.name})


@router.delete("/products/{product_id}", summary="删除商品")
def delete_product(
    product_id: int,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    merchant_service.delete_product(db, merchant, product_id)
    return success()


@router.patch("/products/{product_id}/status", summary="上下架")
def set_product_status(
    product_id: int,
    payload: ProductStatusIn,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    product = merchant_service.set_product_status(db, merchant, product_id, payload.is_active)
    return success({"id": product.id, "is_active": product.is_active})


@router.get("/orders", summary="我的订单")
def list_orders(
    status: str | None = Query(default="all"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    items, total = merchant_service.list_orders(
        db, merchant, None if status == "all" else status, page, size
    )
    return success(PageData.build(items, total, page, size))
