"""Add activity hub columns to activity_templates

Revision ID: 20260203_hub
Revises: 20260203_followup
Create Date: 2026-02-03

"""
from alembic import op
from sqlalchemy import text

revision = '20260203_hub'
down_revision = '20260203_followup'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("ALTER TABLE activity_templates ADD COLUMN IF NOT EXISTS created_by_user_id UUID"))
    op.execute(text("ALTER TABLE activity_templates ADD COLUMN IF NOT EXISTS scope VARCHAR DEFAULT 'system'"))
    op.execute(text("ALTER TABLE activity_templates ADD COLUMN IF NOT EXISTS adoption_count INTEGER DEFAULT 0"))


def downgrade() -> None:
    op.execute(text("ALTER TABLE activity_templates DROP COLUMN IF EXISTS created_by_user_id"))
    op.execute(text("ALTER TABLE activity_templates DROP COLUMN IF EXISTS scope"))
    op.execute(text("ALTER TABLE activity_templates DROP COLUMN IF EXISTS adoption_count"))
