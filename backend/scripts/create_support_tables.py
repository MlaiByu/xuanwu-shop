"""建智能客服工单表（幂等）。

    .venv/Scripts/python.exe -m scripts.create_support_tables

项目已有 Alembic，这个脚本只用于本地快速起表；正式变更仍应走 alembic revision。
"""

from sqlalchemy import inspect

from app.database import Base, engine
from app.models.support_ticket import SupportTicket


def main() -> int:
    inspector = inspect(engine)
    if SupportTicket.__tablename__ in inspector.get_table_names():
        print(f"表 {SupportTicket.__tablename__} 已存在，跳过")
        return 0
    Base.metadata.create_all(bind=engine, tables=[SupportTicket.__table__])
    print(f"已创建表 {SupportTicket.__tablename__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
