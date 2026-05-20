"""Add missing property columns (lokalisering_id and others)

Revision ID: 20260223_prop_cols
Revises: 8be2957122b1
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = '20260223_prop_cols'
down_revision = '8be2957122b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='lokalisering_id') THEN
                ALTER TABLE properties ADD COLUMN lokalisering_id VARCHAR;
                CREATE INDEX ix_properties_lokalisering_id ON properties(lokalisering_id);
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='owner_name') THEN
                ALTER TABLE properties ADD COLUMN owner_name VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='org_number') THEN
                ALTER TABLE properties ADD COLUMN org_number VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='regulation_type') THEN
                ALTER TABLE properties ADD COLUMN regulation_type VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='project_phase') THEN
                ALTER TABLE properties ADD COLUMN project_phase VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='project_comments') THEN
                ALTER TABLE properties ADD COLUMN project_comments VARCHAR;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='full_address') THEN
                ALTER TABLE properties ADD COLUMN full_address JSONB;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='properties' AND column_name='crisis_contacts') THEN
                ALTER TABLE properties ADD COLUMN crisis_contacts JSONB;
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        DROP INDEX IF EXISTS ix_properties_lokalisering_id;
        ALTER TABLE properties DROP COLUMN IF EXISTS lokalisering_id;
        ALTER TABLE properties DROP COLUMN IF EXISTS owner_name;
        ALTER TABLE properties DROP COLUMN IF EXISTS org_number;
        ALTER TABLE properties DROP COLUMN IF EXISTS regulation_type;
        ALTER TABLE properties DROP COLUMN IF EXISTS project_phase;
        ALTER TABLE properties DROP COLUMN IF EXISTS project_comments;
        ALTER TABLE properties DROP COLUMN IF EXISTS full_address;
        ALTER TABLE properties DROP COLUMN IF EXISTS crisis_contacts;
    """))
