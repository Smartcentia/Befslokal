"""Add parent_unit_id_erp for avdeling-institusjon kobling (e-don2 TilhørighetEnhetID)

Revision ID: 20260224_parent_unit_id
Revises: 20260203_edon2_avdeling
Create Date: 2026-02-24

"""
from alembic import op
from sqlalchemy.sql import text

revision = '20260224_parent_unit_id'
down_revision = '20260203_edon2_avdeling'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='properties' AND column_name='parent_unit_id_erp'
            ) THEN
                ALTER TABLE properties ADD COLUMN parent_unit_id_erp VARCHAR;
            END IF;
        END
        $$;
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_properties_parent_unit_id_erp ON properties(parent_unit_id_erp);"
    ))


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS ix_properties_parent_unit_id_erp;"))
    op.execute(text("ALTER TABLE properties DROP COLUMN IF EXISTS parent_unit_id_erp;"))
