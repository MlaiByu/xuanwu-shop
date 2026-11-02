"""订单超时后台任务（需求 §5.3）。

单进程内线程实现，条件更新保证幂等，即使多跑也只会成功一次。
生产多 worker 环境建议迁移到 Celery/APScheduler。
"""
import logging
import threading
import time

from app.config import settings
from app.database import SessionLocal
from app.services import order_service

logger = logging.getLogger("xuanwu.scheduler")


def _tick() -> None:
    db = SessionLocal()
    start = time.perf_counter()
    try:
        order_service.expire_pending_orders(db)
        order_service.auto_confirm_shipped_orders(db)
    finally:
        db.close()
    cost_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info("scheduler tick done cost_ms=%s", cost_ms)


def _loop() -> None:
    while True:
        time.sleep(60)
        try:
            _tick()
        except Exception:
            logger.exception("scheduler tick failed")


def start_scheduler() -> None:
    if not settings.order_expire_job_enabled:
        return
    thread = threading.Thread(target=_loop, name="order-expire-job", daemon=True)
    thread.start()
