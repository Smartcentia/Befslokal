"""add_missing_property_fields_and_association

Revision ID: e37b8113d0ea
Revises: 5f8a0d7ecf8e
Create Date: 2026-01-30 00:37:04.894248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e37b8113d0ea'
down_revision: Union[str, Sequence[str], None] = '5f8a0d7ecf8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure properties table has all expected columns
    # We use IF NOT EXISTS for maximum safety in environments where partial changes exist
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS name VARCHAR"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS usage VARCHAR"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS total_area DOUBLE PRECISION"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS construction_year INTEGER"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS energy_label VARCHAR"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS municipality VARCHAR"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS municipality_code VARCHAR"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS gnr INTEGER"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS bnr INTEGER"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS approved_places INTEGER"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS region VARCHAR"))
    op.execute(sa.text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS external_data JSONB"))

    # 2. Add some helpful indexes
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_properties_name ON properties(name)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_properties_region ON properties(region)"))

    # 3. Ensure user_property_association table exists
    # Check for column existence before creating FK constraints
    op.execute(sa.text("""
        DO $$
        DECLARE
            has_user_id BOOLEAN;
            has_property_id BOOLEAN;
        BEGIN
            -- Check if target columns exist
            has_user_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'users'
                    AND column_name = 'user_id'
            );
            has_property_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'properties'
                    AND column_name = 'property_id'
            );

            -- Only create table if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'user_property_association'
            ) THEN
                IF has_user_id AND has_property_id THEN
                    CREATE TABLE user_property_association (
                        user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                        property_id UUID REFERENCES properties(property_id) ON DELETE CASCADE,
                        PRIMARY KEY (user_id, property_id)
                    );
                ELSIF has_user_id THEN
                    CREATE TABLE user_property_association (
                        user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                        property_id UUID,
                        PRIMARY KEY (user_id, property_id)
                    );
                ELSIF has_property_id THEN
                    CREATE TABLE user_property_association (
                        user_id UUID,
                        property_id UUID REFERENCES properties(property_id) ON DELETE CASCADE,
                        PRIMARY KEY (user_id, property_id)
                    );
                ELSE
                    CREATE TABLE user_property_association (
                        user_id UUID,
                        property_id UUID,
                        PRIMARY KEY (user_id, property_id)
                    );
                END IF;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    # Drop association table first
    op.execute(sa.text("DROP TABLE IF EXISTS user_property_association"))
    
    # Drop added columns
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS name"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS usage"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS total_area"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS construction_year"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS energy_label"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS municipality"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS municipality_code"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS gnr"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS bnr"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS approved_places"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS region"))
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS external_data"))
