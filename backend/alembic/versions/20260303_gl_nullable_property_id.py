"""make gl_transactions.property_id nullable + add missing columns

Revision ID: 20260303_gl_nullable
Revises: f98b219a34e8
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa

revision = '20260303_gl_nullable'
down_revision = 'f98b219a34e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Make property_id nullable (was NOT NULL in some DB states)
    conn.execute(sa.text(
        "ALTER TABLE gl_transactions ALTER COLUMN property_id DROP NOT NULL"
    ))

    # Add missing columns (IF NOT EXISTS = safe to re-run)
    missing_cols = [
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS year INTEGER",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS month INTEGER",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS description VARCHAR(500)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS vendor VARCHAR(200)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS source_system VARCHAR(50)",
    ]
    for sql in missing_cols:
        conn.execute(sa.text(sql))

    # Indexes for new columns
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_gl_year ON gl_transactions(year)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_gl_source_system ON gl_transactions(source_system)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_gl_category ON gl_transactions(category)"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_gl_category"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_gl_source_system"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_gl_year"))
    conn.execute(sa.text("ALTER TABLE gl_transactions DROP COLUMN IF EXISTS source_system"))
    conn.execute(sa.text("ALTER TABLE gl_transactions DROP COLUMN IF EXISTS vendor"))
    conn.execute(sa.text("ALTER TABLE gl_transactions DROP COLUMN IF EXISTS description"))
    conn.execute(sa.text("ALTER TABLE gl_transactions DROP COLUMN IF EXISTS category"))
    conn.execute(sa.text("ALTER TABLE gl_transactions DROP COLUMN IF EXISTS month"))
    conn.execute(sa.text("ALTER TABLE gl_transactions DROP COLUMN IF EXISTS year"))
