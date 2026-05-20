"""Add is_active column to users for soft delete

Revision ID: 20260203_is_active
Revises: 838e50a243c0
Create Date: 2026-02-03

"""
from alembic import op
from sqlalchemy import text

revision = '20260203_is_active'
down_revision = '838e50a243c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true"))


def downgrade() -> None:
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS is_active"))
