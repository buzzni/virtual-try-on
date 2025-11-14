"""add user contact and terms fields

Revision ID: 1f0b3a0b4c4e
Revises: f9c1884d783e
Create Date: 2025-01-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1f0b3a0b4c4e'
down_revision: Union[str, None] = 'f9c1884d783e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(32)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_name TEXT")
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_agreed BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_agreed BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_agreed BOOLEAN NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS marketing_agreed")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS privacy_agreed")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS terms_agreed")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS organization_name")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone_number")
