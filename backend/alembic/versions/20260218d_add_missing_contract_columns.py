"""add missing contract columns (start_date, end_date, category, cost fields)

Revision ID: 20260218d_add_contract_cols
Revises: 20260218c_convert_enums
Create Date: 2026-02-18
"""
from alembic import op

revision = '20260218d_add_contract_cols'
down_revision = '20260218c_convert_enums'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS category TEXT")
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS start_date DATE")
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS end_date DATE")
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS caretaker_cost DOUBLE PRECISION")
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS cleaning_cost DOUBLE PRECISION")
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS parking_cost DOUBLE PRECISION")
    op.execute("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS card_reader_cost DOUBLE PRECISION")
    op.execute("CREATE INDEX IF NOT EXISTS ix_contracts_category ON contracts (category)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_contracts_start_date ON contracts (start_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_contracts_end_date ON contracts (end_date)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_contracts_end_date")
    op.execute("DROP INDEX IF EXISTS ix_contracts_start_date")
    op.execute("DROP INDEX IF EXISTS ix_contracts_category")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS card_reader_cost")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS parking_cost")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS cleaning_cost")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS caretaker_cost")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS end_date")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS start_date")
    op.execute("ALTER TABLE contracts DROP COLUMN IF EXISTS category")
