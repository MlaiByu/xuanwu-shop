"""业务错误码与业务异常（需求 §2.1、§2.2）。

约定：HTTP 状态码表达请求层结果，body.code 表达业务结果，两者必须成对出现。
"""
from enum import IntEnum

from fastapi import status


class ErrorCode(IntEnum):
    SUCCESS = 0
    PARAM_INVALID = 40001
    PARAM_CONFLICT = 40002
    UNAUTHENTICATED = 40100
    TOKEN_INVALID = 40101
    FORBIDDEN = 40300
    NOT_FOUND = 40400
    ALREADY_EXISTS = 40900
    STOCK_NOT_ENOUGH = 40901
    STATE_UNAVAILABLE = 40902
    DUPLICATE_SUBMIT = 40903
    SERVER_ERROR = 50000


HTTP_STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.SUCCESS: status.HTTP_200_OK,
    ErrorCode.PARAM_INVALID: status.HTTP_400_BAD_REQUEST,
    ErrorCode.PARAM_CONFLICT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.UNAUTHENTICATED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.STOCK_NOT_ENOUGH: status.HTTP_409_CONFLICT,
    ErrorCode.STATE_UNAVAILABLE: status.HTTP_409_CONFLICT,
    ErrorCode.DUPLICATE_SUBMIT: status.HTTP_409_CONFLICT,
    ErrorCode.SERVER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

DEFAULT_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.SUCCESS: "ok",
    ErrorCode.PARAM_INVALID: "参数校验失败",
    ErrorCode.PARAM_CONFLICT: "参数逻辑冲突",
    ErrorCode.UNAUTHENTICATED: "请先登录",
    ErrorCode.TOKEN_INVALID: "登录凭证无效或已过期",
    ErrorCode.FORBIDDEN: "权限不足",
    # 归属校验失败同样使用该码，避免泄露资源是否存在
    ErrorCode.NOT_FOUND: "资源不存在",
    ErrorCode.ALREADY_EXISTS: "资源已存在",
    ErrorCode.STOCK_NOT_ENOUGH: "库存不足",
    ErrorCode.STATE_UNAVAILABLE: "当前状态不支持该操作",
    ErrorCode.DUPLICATE_SUBMIT: "请勿重复提交",
    ErrorCode.SERVER_ERROR: "服务器内部错误",
}


class BizException(Exception):
    """业务异常。

    抛出时只传业务码，HTTP 状态码由映射表决定，杜绝"200 + 业务错误码"的写法。
    """

    def __init__(self, code: ErrorCode, message: str | None = None, data: dict | None = None):
        self.code = code
        self.message = message or DEFAULT_MESSAGES[code]
        self.data = data
        self.http_status = HTTP_STATUS_BY_CODE[code]
        super().__init__(self.message)
