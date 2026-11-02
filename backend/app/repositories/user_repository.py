from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.scalar(select(User).where(User.phone == phone))

    def get_by_account(self, account: str) -> User | None:
        account = account.strip()
        if "@" in account:
            return self.get_by_email(account)
        return self.get_by_phone(account)

    def email_or_phone_exists(self, email: str, phone: str | None) -> str | None:
        """返回冲突字段名，无冲突返回 None。"""
        conditions = [User.email == email.lower()]
        if phone:
            conditions.append(User.phone == phone)
        existing = self.db.scalar(select(User).where(or_(*conditions)).limit(1))
        if existing is None:
            return None
        if existing.email == email.lower():
            return "email"
        return "phone"

    def create(
        self,
        email: str,
        hashed_password: str,
        nickname: str,
        phone: str | None = None,
        is_admin: bool = False,
        role: str = User.ROLE_CUSTOMER,
    ) -> User:
        user = User(
            email=email.lower(),
            phone=phone,
            hashed_password=hashed_password,
            nickname=nickname,
            is_admin=is_admin,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
