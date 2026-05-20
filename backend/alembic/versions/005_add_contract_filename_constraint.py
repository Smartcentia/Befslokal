"""Add contract filename constraint for unique region+type+number

Revision ID: 005_contract_filename
Revises: ('004_add_external_data_column', 'a1b2c3d4e5f6')
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '005_contract_filename'
down_revision = ('004_add_external_data_column', 'a1b2c3d4e5f6')  # Merge two branches
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All operations wrapped in table existence check
    op.execute(text("""
        DO $$
        BEGIN
            -- Only proceed if contracts table exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'contracts'
            ) THEN
                -- Add columns for filename components (nullable for existing data)
                ALTER TABLE contracts
                ADD COLUMN IF NOT EXISTS filename_region VARCHAR(10),
                ADD COLUMN IF NOT EXISTS filename_type VARCHAR(10),
                ADD COLUMN IF NOT EXISTS filename_number INTEGER;

                -- Update existing rows based on external_data->>'filnavn' if available
                -- Uses parse_contract_filename logic via SQL
                UPDATE contracts
                SET
                    filename_region = CASE
                        WHEN external_data->>'filnavn' ~ '^(SØR|VEST|NORD|ØST)-'
                        THEN SUBSTRING(external_data->>'filnavn' FROM '^(SØR|VEST|NORD|ØST)')
                        ELSE NULL
                    END,
                    filename_type = CASE
                        WHEN external_data->>'filnavn' ~ '^[^-]+-([^-]+)-'
                        THEN SUBSTRING(external_data->>'filnavn' FROM '^[^-]+-([^-]+)-')
                        ELSE NULL
                    END,
                    filename_number = CASE
                        WHEN external_data->>'filnavn' ~ '^[^-]+-[^-]+-([0-9]{6})'
                        THEN CAST(SUBSTRING(external_data->>'filnavn' FROM '^[^-]+-[^-]+-([0-9]{6})') AS INTEGER)
                        ELSE NULL
                    END
                WHERE external_data->>'filnavn' IS NOT NULL;

                -- Create unique constraint on region+type+number (only for non-null values)
                -- Uses partial unique index to allow NULL values
                CREATE UNIQUE INDEX IF NOT EXISTS ix_contracts_filename_unique
                ON contracts (filename_region, filename_type, filename_number)
                WHERE filename_region IS NOT NULL
                  AND filename_type IS NOT NULL
                  AND filename_number IS NOT NULL;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    # Drop index and columns only if contracts table exists
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'contracts'
            ) THEN
                -- Drop index
                DROP INDEX IF EXISTS ix_contracts_filename_unique;

                -- Drop columns
                ALTER TABLE contracts
                DROP COLUMN IF EXISTS filename_region,
                DROP COLUMN IF EXISTS filename_type,
                DROP COLUMN IF EXISTS filename_number;
            END IF;
        END $$;
    """))
