"""expand role column to VARCHAR(32) for new roles

Revision ID: 20260509_expand_role
Revises:
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = '20260509_expand_role'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'users', 'role',
        existing_type=sa.String(16),
        type_=sa.String(32),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'users', 'role',
        existing_type=sa.String(32),
        type_=sa.String(16),
        existing_nullable=True,
    )
