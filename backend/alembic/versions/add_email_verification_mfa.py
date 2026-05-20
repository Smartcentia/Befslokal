"""Add email verification and MFA

Revision ID: add_email_verification_mfa
Revises: scheduled_activities_2026_01_10
Create Date: 2026-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_email_verification_mfa'
down_revision = 'scheduled_activities_2026_01_10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ensure users table exists (since it's not created in 001_initial)
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            email VARCHAR NOT NULL,
            name VARCHAR,
            role VARCHAR,
            region VARCHAR,
            email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            mfa_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            mfa_verified_at TIMESTAMP WITH TIME ZONE
        )
    """))
    op.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email)"))

    # 2. Ensure user_property_association table exists
    # Check for column existence before creating FK constraints
    op.execute(text("""
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

    # 3. Add columns if they were missing (redundant for new tables, but safe for existing ones)
    op.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE"))
    op.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN NOT NULL DEFAULT TRUE"))
    op.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_verified_at TIMESTAMP WITH TIME ZONE"))
    
    # Create email_verification_codes table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS email_verification_codes (
            id VARCHAR PRIMARY KEY,
            email VARCHAR NOT NULL,
            code_hash VARCHAR NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_email_verification_codes_email ON email_verification_codes(email)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_email_verification_codes_email_expires ON email_verification_codes(email, expires_at)"))
    
    # Create mfa_tokens table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS mfa_tokens (
            token VARCHAR PRIMARY KEY,
            user_email VARCHAR NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_mfa_tokens_user_email ON mfa_tokens(user_email)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_mfa_tokens_user_email_expires ON mfa_tokens(user_email, expires_at)"))
    
    # Grandfather existing users: set email_verified=True and mfa_verified_at=NOW()
    # Only run if email_verified is actually a BOOLEAN column
    op.execute(text("""
        DO $$
        DECLARE
            col_type TEXT;
        BEGIN
            -- Get the data type of email_verified column
            SELECT data_type INTO col_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = 'users'
                AND column_name = 'email_verified';

            -- Only update if column exists and is boolean type
            IF col_type = 'boolean' THEN
                UPDATE users
                SET email_verified = TRUE,
                    mfa_verified_at = NOW()
                WHERE email_verified = FALSE;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    # Drop tables
    op.execute(text("DROP TABLE IF EXISTS mfa_tokens"))
    op.execute(text("DROP TABLE IF EXISTS email_verification_codes"))
    
    # Remove columns from users table
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS mfa_verified_at"))
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS mfa_enabled"))
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS email_verified"))
