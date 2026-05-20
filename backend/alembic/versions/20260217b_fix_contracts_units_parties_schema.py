"""Fix contracts, units, parties tables for FastAPI compatibility

Same Prisma/Better Auth schema issue as users/properties:
DB has 'id' (TEXT) as PK, FastAPI models expect 'contract_id'/'unit_id'/'party_id' (UUID).

Revision ID: 20260217b_fix_core_tables
Revises: 20260217_fix_users_schema
Create Date: 2026-02-17
"""
from alembic import op
from sqlalchemy import text

revision = '20260217b_fix_core_tables'
down_revision = '20260220_internal_control_cases'
branch_labels = None
depends_on = None


def _add_uuid_id_column(table: str, col: str) -> str:
    """Returns SQL snippet to add a UUID column with unique index and id default."""
    return f"""
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = '{table}'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = '{table}'
                        AND column_name = '{col}'
                ) THEN
                    ALTER TABLE {table} ADD COLUMN {col} UUID DEFAULT gen_random_uuid() NOT NULL;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'public'
                        AND tablename = '{table}'
                        AND indexname = 'ix_{table}_{col}'
                ) THEN
                    CREATE UNIQUE INDEX ix_{table}_{col} ON {table}({col});
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = '{table}'
                        AND column_name = 'id'
                ) THEN
                    ALTER TABLE {table} ALTER COLUMN id
                        SET DEFAULT 'befs_' || replace(gen_random_uuid()::text, '-', '');
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = '{table}'
                        AND column_name = 'organization_id'
                ) THEN
                    ALTER TABLE {table} ALTER COLUMN organization_id DROP NOT NULL;
                END IF;

                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = '{table}'
                        AND column_name = 'updated_at'
                        AND is_nullable = 'NO'
                ) THEN
                    ALTER TABLE {table} ALTER COLUMN updated_at SET DEFAULT NOW();
                    UPDATE {table} SET updated_at = NOW() WHERE updated_at IS NULL;
                END IF;
            END IF;
"""


def upgrade() -> None:
    op.execute(text(f"""
        DO $$
        BEGIN
            {_add_uuid_id_column('contracts', 'contract_id')}
            {_add_uuid_id_column('units', 'unit_id')}
            {_add_uuid_id_column('parties', 'party_id')}
        END $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            DROP INDEX IF EXISTS ix_contracts_contract_id;
            ALTER TABLE contracts DROP COLUMN IF EXISTS contract_id;

            DROP INDEX IF EXISTS ix_units_unit_id;
            ALTER TABLE units DROP COLUMN IF EXISTS unit_id;

            DROP INDEX IF EXISTS ix_parties_party_id;
            ALTER TABLE parties DROP COLUMN IF EXISTS party_id;
        END $$;
    """))
