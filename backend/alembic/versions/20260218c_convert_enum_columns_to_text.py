"""convert enum columns to text (remove PG ENUM types)

Revision ID: 20260218c_convert_enums
Revises: 20260218b_create_file_meta
Create Date: 2026-02-18
"""
from alembic import op

revision = '20260218c_convert_enums'
down_revision = '20260218b_create_file_meta'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            -- Convert contracts.status from contractstatus ENUM to TEXT
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'contracts'
                  AND column_name = 'status'
                  AND udt_name = 'contractstatus'
            ) THEN
                ALTER TABLE contracts ALTER COLUMN status TYPE TEXT USING status::TEXT;
            END IF;

            -- Drop the contractstatus ENUM type if it exists
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contractstatus') THEN
                DROP TYPE contractstatus;
            END IF;

            -- Convert ai_tools.status from toolstatus ENUM to TEXT
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'ai_tools'
                  AND column_name = 'status'
                  AND udt_name = 'toolstatus'
            ) THEN
                ALTER TABLE ai_tools ALTER COLUMN status TYPE TEXT USING status::TEXT;
            END IF;

            -- Drop the toolstatus ENUM type if it exists
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'toolstatus') THEN
                DROP TYPE toolstatus;
            END IF;

            -- Convert ai_tools.qa_status from qastatus ENUM to TEXT
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'ai_tools'
                  AND column_name = 'qa_status'
                  AND udt_name = 'qastatus'
            ) THEN
                ALTER TABLE ai_tools ALTER COLUMN qa_status TYPE TEXT USING qa_status::TEXT;
            END IF;

            -- Drop the qastatus ENUM type if it exists
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'qastatus') THEN
                DROP TYPE qastatus;
            END IF;
        END$$;
    """)


def downgrade():
    pass  # No downgrade - TEXT is compatible with the old ENUM values
