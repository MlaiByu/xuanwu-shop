"""创建超级管理员账号（A 端最高权限）。

用法（在 backend 目录下）：
    .venv/Scripts/python.exe -m scripts.create_admin admin@example.com Admin1234
"""
import sys

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    email, password = sys.argv[1], sys.argv[2]

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if repo.get_by_email(email):
            print(f"邮箱已存在：{email}")
            return 1
        user = repo.create(
            email=email,
            hashed_password=hash_password(password),
            nickname="超级管理员",
            is_admin=True,
            role=User.ROLE_SUPER_ADMIN,
        )
        print(f"超级管理员已创建：id={user.id} email={user.email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
