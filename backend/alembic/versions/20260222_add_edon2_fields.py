"""Add edon2 specific fields to properties table

Revision ID: 20260222_add_edon2_fields
Revises: 20260218_create_notifications_table
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260222_add_edon2_fields'
down_revision = '20260218_create_notifications'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            -- Add columns if they don't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='affiliation') THEN
                ALTER TABLE properties ADD COLUMN affiliation VARCHAR;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='budgeted_places') THEN
                ALTER TABLE properties ADD COLUMN budgeted_places INTEGER;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='legal_basis') THEN
                ALTER TABLE properties ADD COLUMN legal_basis VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='closed_at') THEN
                ALTER TABLE properties ADD COLUMN closed_at TIMESTAMP;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='ownership_type') THEN
                ALTER TABLE properties ADD COLUMN ownership_type VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='unit_id_erp') THEN
                ALTER TABLE properties ADD COLUMN unit_id_erp VARCHAR;
                CREATE INDEX ix_properties_unit_id_erp ON properties(unit_id_erp);
            END IF;
        END
        $$;
    """))

def downgrade() -> None:
    op.execute(text("""
        ALTER TABLE properties DROP COLUMN IF EXISTS affiliation;
        ALTER TABLE properties DROP COLUMN IF EXISTS budgeted_places;
        ALTER TABLE properties DROP COLUMN IF EXISTS legal_basis;
        ALTER TABLE properties DROP COLUMN IF EXISTS closed_at;
        ALTER TABLE properties DROP COLUMN IF EXISTS ownership_type;
        DROP INDEX IF EXISTS ix_properties_unit_id_erp;
        ALTER TABLE properties DROP COLUMN IF EXISTS unit_id_erp;
    """))
