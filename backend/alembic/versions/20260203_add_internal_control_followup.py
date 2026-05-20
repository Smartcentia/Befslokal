"""Add follow-up columns to internal_control_cases

Revision ID: 20260203_followup
Revises: 189fd0945244
Create Date: 2026-02-03

"""
from alembic import op
from sqlalchemy import text


def _table_exists(table_name: str) -> bool:
    """Return True if table exists, else False."""
    conn = op.get_bind()
    result = conn.execute(text("SELECT to_regclass(:tbl)"), {"tbl": f"public.{table_name}"}).scalar()
    return result is not None

revision = '20260203_followup'
down_revision = '189fd0945244'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not _table_exists("internal_control_cases"):
        # Fresh databases may not have this feature table yet; skip safely.
        return
    op.execute(text("ALTER TABLE internal_control_cases ADD COLUMN IF NOT EXISTS follow_up_status VARCHAR DEFAULT 'none'"))
    op.execute(text("ALTER TABLE internal_control_cases ADD COLUMN IF NOT EXISTS last_reminder_at TIMESTAMP WITH TIME ZONE"))
    op.execute(text("ALTER TABLE internal_control_cases ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP WITH TIME ZONE"))


def downgrade() -> None:
    if not _table_exists("internal_control_cases"):
        return
    op.execute(text("ALTER TABLE internal_control_cases DROP COLUMN IF EXISTS follow_up_status"))
    op.execute(text("ALTER TABLE internal_control_cases DROP COLUMN IF EXISTS last_reminder_at"))
    op.execute(text("ALTER TABLE internal_control_cases DROP COLUMN IF EXISTS escalated_at"))
