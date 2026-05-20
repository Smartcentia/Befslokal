"""add_user_property_association_table

Revision ID: 5f8a0d7ecf8e
Revises: 189fd0945244
Create Date: 2026-01-30 00:27:36.797679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f8a0d7ecf8e'
down_revision: Union[str, Sequence[str], None] = '189fd0945244'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure user_property_association table exists
    # This migration explicitly adds the junction table that was missing in some environments
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
    op.execute(sa.text("DROP TABLE IF EXISTS user_property_association"))
