"""Add user columns to checklist_templates

Revision ID: 20260203_checklist
Revises: 20260203_hub
Create Date: 2026-02-03

"""
from alembic import op
from sqlalchemy import text


def _table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(text("SELECT to_regclass(:tbl)"), {"tbl": f"public.{table_name}"}).scalar()
    return result is not None

revision = '20260203_checklist'
down_revision = '20260203_hub'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not _table_exists("checklist_templates"):
        return
    op.execute(text("ALTER TABLE checklist_templates ADD COLUMN IF NOT EXISTS created_by_user_id UUID"))
    op.execute(text("ALTER TABLE checklist_templates ADD COLUMN IF NOT EXISTS scope VARCHAR DEFAULT 'system'"))


def downgrade() -> None:
    if not _table_exists("checklist_templates"):
        return
    op.execute(text("ALTER TABLE checklist_templates DROP COLUMN IF EXISTS created_by_user_id"))
    op.execute(text("ALTER TABLE checklist_templates DROP COLUMN IF EXISTS scope"))
