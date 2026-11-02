"""add token_version to users

Revision ID: b7c9d1e2f3a4
Revises: 97f807addb9c
Create Date: 2026-11-01 00:46:00+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c9d1e2f3a4'
down_revision: Union[str, None] = '97f807addb9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 凭证版本号：改密/封禁 +1，已签发 token 立即失效（审查报告 M1）
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('token_version', sa.Integer(), nullable=False, server_default='0')
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('token_version')
