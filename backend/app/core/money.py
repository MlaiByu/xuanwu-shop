"""通用小工具：金额格式化与 LIKE 转义。"""
from decimal import ROUND_HALF_UP, Decimal


def format_price(value: Decimal | float | int | str | None) -> str:
    """金额统一输出为两位小数字符串（需求 §2.4）。

    禁止使用 float 直接参与金额运算；此处仅做展示格式化。
    """
    if value is None:
        return "0.00"
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return str(amount)


def to_decimal(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def escape_like(keyword: str) -> str:
    """转义 LIKE 通配符，避免用户输入 % / _ 改变匹配语义。"""
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
