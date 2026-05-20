"""Fix users table schema for FastAPI compatibility

The users table was created by Better Auth/Prisma with:
  - id (TEXT CUID) as primary key
  - email_verified (TIMESTAMP) - Better Auth style
  - organization_id (TEXT) - multi-tenant field

FastAPI SQLAlchemy model expects:
  - user_id (UUID) as primary key
  - email_verified (BOOLEAN)
  - region (VARCHAR)

This migration adds the missing columns and fixes type mismatches
without breaking the existing Better Auth schema.

Revision ID: 20260217_fix_users_schema
Revises: merge_cbb_af84
Create Date: 2026-02-17
"""
from alembic import op
from sqlalchemy import text

revision = '20260217_fix_users_schema'
down_revision = 'merge_cbb_af84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        DO $$
        DECLARE
            col_type TEXT;
        BEGIN
            -- Only proceed if users table exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'users'
            ) THEN

                -- 1. Add user_id UUID column (FastAPI model primary key)
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'users'
                        AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE users ADD COLUMN user_id UUID DEFAULT gen_random_uuid() NOT NULL;
                END IF;

                -- 2. Create unique index on user_id if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'public'
                        AND tablename = 'users'
                        AND indexname = 'ix_users_user_id'
                ) THEN
                    CREATE UNIQUE INDEX ix_users_user_id ON users(user_id);
                END IF;

                -- 3. Fix email_verified: convert TIMESTAMP to BOOLEAN
                --    Better Auth stores NULL (unverified) or a timestamp (when verified)
                --    FastAPI model expects BOOLEAN: FALSE (unverified) or TRUE (verified)
                SELECT data_type INTO col_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'users'
                    AND column_name = 'email_verified';

                IF col_type IN ('timestamp without time zone', 'timestamp with time zone') THEN
                    -- Add a temp boolean column
                    ALTER TABLE users ADD COLUMN email_verified_new BOOLEAN NOT NULL DEFAULT FALSE;
                    -- NULL timestamp → FALSE (not verified), any timestamp → TRUE (verified)
                    UPDATE users SET email_verified_new = (email_verified IS NOT NULL);
                    -- Swap columns
                    ALTER TABLE users DROP COLUMN email_verified;
                    ALTER TABLE users RENAME COLUMN email_verified_new TO email_verified;
                END IF;

                -- 4. Add region column if missing (FastAPI model uses this)
                ALTER TABLE users ADD COLUMN IF NOT EXISTS region VARCHAR;

                -- 5. Set a default for the id column so FastAPI can insert new users
                --    Only present on Better Auth schema (FastAPI model uses user_id, not id)
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'users'
                        AND column_name = 'id'
                ) THEN
                    ALTER TABLE users ALTER COLUMN id SET DEFAULT
                        'befs_' || replace(gen_random_uuid()::text, '-', '');
                END IF;

                -- 6. Make Better Auth-specific NOT NULL columns nullable for FastAPI compat
                --    FastAPI model doesn't manage organization_id (Better Auth concept)
                --    Only present on Better Auth schema, skip if column doesn't exist
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'users'
                        AND column_name = 'organization_id'
                ) THEN
                    ALTER TABLE users ALTER COLUMN organization_id DROP NOT NULL;
                END IF;
                --    updated_at needs a default so FastAPI inserts don't fail
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'users'
                        AND column_name = 'updated_at'
                ) THEN
                    ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT NOW();
                    UPDATE users SET updated_at = NOW() WHERE updated_at IS NULL;
                END IF;
                --    Normalize role values: Better Auth uses 'admin'/'user' (lowercase)
                --    FastAPI UserRole enum uses 'ADMIN'/'PROPERTY_MANAGER' (uppercase)
                UPDATE users SET role = CASE
                    WHEN role = 'admin' THEN 'ADMIN'
                    WHEN role = 'user' THEN 'PROPERTY_MANAGER'
                    WHEN role = 'moderator' THEN 'REGIONAL_MANAGER'
                    ELSE UPPER(role)
                END
                WHERE role NOT IN ('ADMIN', 'REGIONAL_MANAGER', 'PROPERTY_MANAGER', 'JANITOR');

            END IF;

            -- Fix properties table: same Better Auth / Prisma schema issue
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'properties'
            ) THEN

                -- Add property_id UUID column (FastAPI model primary key)
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'properties'
                        AND column_name = 'property_id'
                ) THEN
                    ALTER TABLE properties ADD COLUMN property_id UUID DEFAULT gen_random_uuid() NOT NULL;
                END IF;

                -- Create unique index on property_id if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'public'
                        AND tablename = 'properties'
                        AND indexname = 'ix_properties_property_id'
                ) THEN
                    CREATE UNIQUE INDEX ix_properties_property_id ON properties(property_id);
                END IF;

                -- Set default for properties.id so FastAPI can create properties
                -- Only present on Better Auth schema
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'properties'
                        AND column_name = 'id'
                ) THEN
                    ALTER TABLE properties ALTER COLUMN id SET DEFAULT
                        'befs_' || replace(gen_random_uuid()::text, '-', '');
                END IF;

                -- Make Better Auth NOT NULL columns nullable/defaulted for FastAPI compat
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'properties'
                        AND column_name = 'organization_id'
                ) THEN
                    ALTER TABLE properties ALTER COLUMN organization_id DROP NOT NULL;
                END IF;
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'properties'
                        AND column_name = 'updated_at'
                ) THEN
                    ALTER TABLE properties ALTER COLUMN updated_at SET DEFAULT NOW();
                    UPDATE properties SET updated_at = NOW() WHERE updated_at IS NULL;
                END IF;
                -- name is optional in FastAPI model
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = 'properties'
                        AND column_name = 'name'
                ) THEN
                    ALTER TABLE properties ALTER COLUMN name DROP NOT NULL;
                END IF;

            END IF;
        END $$;
    """))


def downgrade() -> None:
    # This migration fixes a schema compatibility issue - not straightforward to reverse.
    # The email_verified column type change cannot be safely reversed without data loss.
    # The user_id column and region column can be dropped if needed.
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'users'
            ) THEN
                DROP INDEX IF EXISTS ix_users_user_id;
                ALTER TABLE users DROP COLUMN IF EXISTS user_id;
                ALTER TABLE users DROP COLUMN IF EXISTS region;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'properties'
            ) THEN
                DROP INDEX IF EXISTS ix_properties_property_id;
                ALTER TABLE properties DROP COLUMN IF EXISTS property_id;
            END IF;
        END $$;
    """))
