"""管理端路由聚合（需求 §8.6）。"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin
from app.api.v1.admin import admins, categories, merchants, orders, products, upload
from app.core.responses import success
from app.models.user import User

# 聚合层加一道鉴权兜底：即使某个子路由忘加自己的依赖，也不会裸奔。
# 子路由可叠加更严格的 super_admin 依赖，二者不冲突（get_current_user 每请求只查一次）。
router = APIRouter(prefix="/admin", tags=["管理端"], dependencies=[Depends(get_current_admin)])
router.include_router(products.router)
router.include_router(categories.router)
router.include_router(orders.router)
router.include_router(upload.router)
router.include_router(admins.router)
router.include_router(merchants.router)


@router.get("/ping", summary="管理端探活（需管理员）")
def admin_ping(admin: User = Depends(get_current_admin)):
    return success({"admin_id": admin.id, "email": admin.email})
