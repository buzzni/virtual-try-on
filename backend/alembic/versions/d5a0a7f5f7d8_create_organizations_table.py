"""create organizations table

Revision ID: d5a0a7f5f7d8
Revises: cc54f1b5d826
Create Date: 2025-01-05 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd5a0a7f5f7d8'
down_revision: Union[str, None] = 'cc54f1b5d826'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_organizations_name', 'organizations', ['name'], unique=False)
    op.create_foreign_key(
        'users_organization_id_fkey',
        source_table='users',
        referent_table='organizations',
        local_cols=['organization_id'],
        remote_cols=['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('users_organization_id_fkey', 'users', type_='foreignkey')
    op.drop_index('ix_organizations_name', table_name='organizations')
    op.drop_table('organizations')
