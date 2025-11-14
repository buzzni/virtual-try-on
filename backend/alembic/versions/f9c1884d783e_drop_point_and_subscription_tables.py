"""drop point and subscription tables

Revision ID: f9c1884d783e
Revises: e913c9f6ef4d
Create Date: 2024-11-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f9c1884d783e'
down_revision: Union[str, None] = 'e913c9f6ef4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('subscription_record')
    op.drop_table('subscriptions')
    op.drop_table('point_usage')
    op.drop_table('points')


def downgrade() -> None:
    op.create_table(
        'points',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('credit', sa.Integer(), nullable=False),
        sa.Column('look_book_ticket', sa.Integer(), nullable=False),
        sa.Column('video_ticket', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    op.create_table(
        'point_usage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('usage_type', sa.String(length=32), nullable=False),
        sa.Column('usage_method', sa.String(length=32), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_point_usage_user', 'point_usage', ['user_id', 'created_at'], unique=False)

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('plan', sa.String(length=64), nullable=True),
        sa.Column('start_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('end_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('next_billing_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('payments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('invoices', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cancel_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'subscription_record',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('subscription_id', sa.UUID(), nullable=True),
        sa.Column('from_plan', sa.String(length=64), nullable=True),
        sa.Column('to_plan', sa.String(length=64), nullable=True),
        sa.Column('payments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
