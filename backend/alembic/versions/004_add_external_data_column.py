"""Add external_data column to properties, units, contracts, parties

Revision ID: 004_add_external_data_column
Revises: d4e9de624aec
Create Date: 2024-11-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '004_add_external_data_column'
down_revision = 'd4e9de624aec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add external_data column to multiple tables, only if tables exist
    op.execute(text("""
        DO $$
        BEGIN
            -- Add to properties table if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'properties'
            ) THEN
                ALTER TABLE properties ADD COLUMN IF NOT EXISTS external_data JSONB;
            END IF;

            -- Add to units table if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'units'
            ) THEN
                ALTER TABLE units ADD COLUMN IF NOT EXISTS external_data JSONB;
            END IF;

            -- Add to contracts table if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'contracts'
            ) THEN
                ALTER TABLE contracts ADD COLUMN IF NOT EXISTS external_data JSONB;
            END IF;

            -- Add to parties table if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'parties'
            ) THEN
                ALTER TABLE parties ADD COLUMN IF NOT EXISTS external_data JSONB;
            END IF;
        END $$;
    """))

    # GIN indexes skipped - not critical and may cause issues with some column types


def downgrade() -> None:
    # Drop columns only if tables exist
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'parties'
            ) THEN
                ALTER TABLE parties DROP COLUMN IF EXISTS external_data;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'contracts'
            ) THEN
                ALTER TABLE contracts DROP COLUMN IF EXISTS external_data;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'units'
            ) THEN
                ALTER TABLE units DROP COLUMN IF EXISTS external_data;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'properties'
            ) THEN
                ALTER TABLE properties DROP COLUMN IF EXISTS external_data;
            END IF;
        END $$;
    """))
