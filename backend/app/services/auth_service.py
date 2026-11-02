"""认证业务逻辑（需求 FR-U-01）。"""
import time

from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest

MAX_FAILURES = 5
WINDOW_SECONDS = 300
LOCK_SECONDS = 600

# 跟踪容量的硬上限：攻击者可以用随机账号名无限刷登录，若不做上限，
# 这两个字典会随请求数单调增长直到进程 OOM（审查报告 M2）。
MAX_TRACKED_ACCOUNTS = 10_000
# 全量清理的间隔：每 256 次写入清一次过期项。
# 不能每次失败都全量扫 1 万条，否则等于用一个 CPU 放大换内存泄漏。
_PRUNE_EVERY = 256

# 登录失败计数与锁定状态。
# 注意：这是进程内实现，仅适用于单 worker 开发环境。
# 多 worker 或重启后计数会丢失，生产环境需迁移到 Redis（见需求 §5.4 已知限制）。
_FAILURES: dict[str, list[float]] = {}
_LOCKED_UNTIL: dict[str, float] = {}
_WRITE_COUNT = 0


def _prune(now: float) -> None:
    """清掉窗口/锁定期已过期的账号记录，回收被随机账号撑大的字典。"""
    for account, records in list(_FAILURES.items()):
        if not records or now - records[-1] >= WINDOW_SECONDS:
            _FAILURES.pop(account, None)

    # 注意不能用「队头未过期就 break」的优化：账号被重复锁定时
    # `_LOCKED_UNTIL[account] = ...` 会保留原插入位置，插入顺序就不再等于过期顺序。
    for account, until in list(_LOCKED_UNTIL.items()):
        if now >= until:
            _LOCKED_UNTIL.pop(account, None)


def _enforce_capacity(now: float) -> None:
    """周期性清理 + 硬上限淘汰，保证字典大小有界且单次开销可控。

    淘汰最早写入的账号意味着极端洪泛下可能挤掉某个账号的失败计数，
    这是"内存有界"换来的已知代价：窗口 5 分钟、上限 1 万，
    要打满 1 万个不同账号才会触发，成本远高于收益。
    """
    global _WRITE_COUNT
    _WRITE_COUNT += 1
    if _WRITE_COUNT % _PRUNE_EVERY == 0:
        _prune(now)

    while len(_FAILURES) > MAX_TRACKED_ACCOUNTS:
        _FAILURES.pop(next(iter(_FAILURES)), None)
    while len(_LOCKED_UNTIL) > MAX_TRACKED_ACCOUNTS:
        _LOCKED_UNTIL.pop(next(iter(_LOCKED_UNTIL)), None)


def _normalize_account(account: str) -> str:
    account = account.strip()
    return account.lower() if "@" in account else account


def _check_locked(account: str) -> None:
    until = _LOCKED_UNTIL.get(account)
    if until is None:
        return
    now = time.monotonic()
    if now < until:
        minutes = int((until - now) / 60) + 1
        raise BizException(ErrorCode.UNAUTHENTICATED, f"尝试过于频繁，请 {minutes} 分钟后重试")
    _LOCKED_UNTIL.pop(account, None)


def _record_failure(account: str) -> None:
    now = time.monotonic()
    records = [t for t in _FAILURES.get(account, []) if now - t < WINDOW_SECONDS]
    records.append(now)
    _FAILURES[account] = records
    if len(records) >= MAX_FAILURES:
        _LOCKED_UNTIL[account] = now + LOCK_SECONDS
        _FAILURES[account] = []
    _enforce_capacity(now)


def _clear_failures(account: str) -> None:
    _FAILURES.pop(account, None)
    _LOCKED_UNTIL.pop(account, None)


def register(db: Session, payload: RegisterRequest) -> User:
    repo = UserRepository(db)
    conflict = repo.email_or_phone_exists(payload.email, payload.phone)
    if conflict == "email":
        raise BizException(ErrorCode.ALREADY_EXISTS, "该邮箱已注册")
    if conflict == "phone":
        raise BizException(ErrorCode.ALREADY_EXISTS, "该手机号已注册")

    nickname = payload.nickname or payload.email.split("@")[0][:20]
    return repo.create(
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        nickname=nickname,
    )


def authenticate(db: Session, account: str, password: str) -> User:
    account = _normalize_account(account)
    _check_locked(account)

    user = UserRepository(db).get_by_account(account)
    # 账号不存在、密码错误、账号停用统一提示，避免账号枚举（AC-U01-4、G5）
    if user is None or not verify_password(password, user.hashed_password) or not user.is_active:
        _record_failure(account)
        raise BizException(ErrorCode.UNAUTHENTICATED, "账号或密码错误")

    _clear_failures(account)
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    """修改当前登录用户的密码。"""
    if not verify_password(old_password, user.hashed_password):
        raise BizException(ErrorCode.UNAUTHENTICATED, "原密码错误")
    if old_password == new_password:
        raise BizException(ErrorCode.PARAM_INVALID, "新密码不能与原密码相同")
    user.hashed_password = hash_password(new_password)
    # 改密后让已签发的其它 token 立即失效（M1）
    user.token_version += 1
    db.commit()
