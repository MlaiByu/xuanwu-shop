from fastapi import APIRouter

from app.api.v1 import addresses, auth, cart, categories, merchant, orders, products, support
from app.api.v1.admin.router import router as admin_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(addresses.router)
api_router.include_router(orders.router)
api_router.include_router(merchant.router)
api_router.include_router(support.router)
api_router.include_router(admin_router)
