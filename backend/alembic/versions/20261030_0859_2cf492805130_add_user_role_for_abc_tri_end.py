"""add user role for ABC tri-end

Revision ID: 2cf492805130
Revises: fd054dd715ca
Create Date: 2026-10-30 08:59:38.714751+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2cf492805130'
down_revision: Union[str, None] = 'fd054dd715ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 先允许 NULL，数据迁移后再收紧为 NOT NULL
    op.add_column('users', sa.Column('role', sa.String(length=16), nullable=True))
    # 数据迁移：现有管理员 → 超级管理员，其余 → 买家
    op.execute("UPDATE users SET role = 'super_admin' WHERE is_admin = true")
    op.execute("UPDATE users SET role = 'customer' WHERE role IS NULL")
    op.alter_column('users', 'role', nullable=False, server_default='customer')


def downgrade() -> None:
    op.drop_column('users', 'role')
