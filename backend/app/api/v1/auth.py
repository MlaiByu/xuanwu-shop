from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.core.responses import success
from app.core.security import COOKIE_NAME, create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="注册")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register(db, payload)
    return success(UserOut.model_validate(user))


@router.post("/login", summary="登录，设置 httpOnly cookie")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload.account, payload.password)
    token, expires_in = create_access_token(user.id, user.is_admin, user.token_version)

    # 凭证放 httpOnly + SameSite=Lax cookie：JS 读不到，XSS 无法窃取（审查报告 M5）。
    # 生产环境走 HTTPS 时加 Secure；SameSite=Lax 阻断跨站 POST，天然防 CSRF。
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=expires_in,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    # 不再在响应体里返回 token，避免前端把凭证写回可被 JS 读取的存储
    return success({"expires_in": expires_in, "user": UserOut.model_validate(user)})


@router.post("/logout", summary="退出登录，清除 cookie")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return success()


@router.get("/me", summary="当前登录用户")
def get_me(user: User = Depends(get_current_user)):
    return success(UserOut.model_validate(user))


@router.post("/change-password", summary="修改密码")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.change_password(db, user, payload.old_password, payload.new_password)
    return success()
