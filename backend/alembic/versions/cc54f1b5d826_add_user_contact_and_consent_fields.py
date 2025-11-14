"""add user contact and consent fields

Revision ID: cc54f1b5d826
Revises: a5c71b03adcf
Create Date: 2025-01-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'cc54f1b5d826'
down_revision: Union[str, None] = 'a5c71b03adcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('required_terms_agreed', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('marketing_terms_agreed', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'organization_id')
    op.drop_column('users', 'marketing_terms_agreed')
    op.drop_column('users', 'required_terms_agreed')
    op.drop_column('users', 'phone_number')
