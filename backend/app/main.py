from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import BASE_DIR, settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import TraceMiddleware, setup_logging
from app.core.responses import success
from app.core.scheduler import start_scheduler

setup_logging(debug=settings.debug)

# 生产环境安全校验：禁止使用默认 JWT secret
if settings.is_production and settings.jwt_secret_key == "change-me-in-production":
    raise RuntimeError("生产环境必须配置 JWT_SECRET_KEY，禁止使用默认值")


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="玄武商城 API",
    description="商品购物平台 MVP。响应契约见需求规格说明书 §2。",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TraceMiddleware)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)

# 上传文件的静态访问
_static_dir = Path(BASE_DIR) / "static"
_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/healthz", tags=["系统"], summary="健康检查")
def healthz():
    return success({"status": "up", "env": settings.app_env})
