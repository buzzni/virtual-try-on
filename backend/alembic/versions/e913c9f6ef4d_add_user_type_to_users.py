"""add user_type to users

Revision ID: e913c9f6ef4d
Revises: d5a0a7f5f7d8
Create Date: 2025-01-05 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e913c9f6ef4d'
down_revision: Union[str, None] = 'd5a0a7f5f7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_type_enum = sa.Enum('user', 'manager', 'admin', name='user_type_enum')


def upgrade() -> None:
    bind = op.get_bind()
    user_type_enum.create(bind, checkfirst=True)
    op.add_column(
        'users',
        sa.Column('user_type', user_type_enum, nullable=False, server_default='user')
    )


def downgrade() -> None:
    op.drop_column('users', 'user_type')
    bind = op.get_bind()
    user_type_enum.drop(bind, checkfirst=True)
