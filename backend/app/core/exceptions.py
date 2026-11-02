"""全局异常处理。

统一出口：任何异常都被转成 {code, message, data}，且 HTTP 状态码与 code 自洽。
500 响应绝不向前端暴露堆栈（需求 §2.2）。
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import DEFAULT_MESSAGES, BizException, ErrorCode
from app.core.responses import error_response

logger = logging.getLogger("xuanwu.error")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizException)
    async def handle_biz_exception(request: Request, exc: BizException):
        return error_response(int(exc.code), exc.http_status, exc.message, exc.data)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            loc = [str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")]
            errors.append({"field": ".".join(loc) or "unknown", "reason": err.get("msg", "")})
        return error_response(
            int(ErrorCode.PARAM_INVALID),
            400,
            DEFAULT_MESSAGES[ErrorCode.PARAM_INVALID],
            {"errors": errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        mapping = {
            401: ErrorCode.UNAUTHENTICATED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            405: ErrorCode.PARAM_INVALID,
        }
        code = mapping.get(exc.status_code)
        if code is not None:
            return error_response(int(code), exc.status_code, DEFAULT_MESSAGES[code])
        if 400 <= exc.status_code < 500:
            # 其余 4xx 保持原状态码，业务码统一归为参数类错误
            return error_response(int(ErrorCode.PARAM_INVALID), exc.status_code, str(exc.detail))
        logger.error("http error %s on %s", exc.status_code, request.url.path)
        return error_response(int(ErrorCode.SERVER_ERROR), exc.status_code, str(exc.detail))

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        # 数据库唯一约束兜底：并发下 service 层预检查竞态会在此兜住（如并发注册同邮箱、并发加购）
        logger.warning("integrity error on %s %s: %s", request.method, request.url.path, exc.orig)
        return error_response(
            int(ErrorCode.ALREADY_EXISTS),
            409,
            "资源冲突，请重试",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        logger.exception("unhandled exception: %s %s", request.method, request.url.path)
        return error_response(
            int(ErrorCode.SERVER_ERROR), 500, DEFAULT_MESSAGES[ErrorCode.SERVER_ERROR]
        )
