"""drop entitlements table

Revision ID: a5c71b03adcf
Revises: db07085767fb
Create Date: 2025-11-12 15:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a5c71b03adcf'
down_revision: Union[str, None] = 'db07085767fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # entitlements 테이블 삭제
    op.drop_table('entitlements')


def downgrade() -> None:
    # entitlements 테이블 복구
    op.create_table(
        'entitlements',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('subscription_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('look_book_remaining', sa.Integer(), server_default='0', nullable=False),
        sa.Column('video_remaining', sa.Integer(), server_default='0', nullable=False),
        sa.Column('credit_cached', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_synced_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
