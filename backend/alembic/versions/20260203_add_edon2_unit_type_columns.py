"""Add unit_short_type and unit_type_derived for avdeling identification (e-don2)

Revision ID: 20260203_edon2_avdeling
Revises: 20260223_prop_cols
Create Date: 2026-02-03

"""
from alembic import op
from sqlalchemy.sql import text

revision = '20260203_edon2_avdeling'
down_revision = '20260223_prop_cols'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='unit_short_type') THEN
                ALTER TABLE properties ADD COLUMN unit_short_type VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='unit_type_derived') THEN
                ALTER TABLE properties ADD COLUMN unit_type_derived VARCHAR;
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        ALTER TABLE properties DROP COLUMN IF EXISTS unit_short_type;
        ALTER TABLE properties DROP COLUMN IF EXISTS unit_type_derived;
    """))
