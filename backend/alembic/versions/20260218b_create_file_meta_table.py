"""create file_meta table

Revision ID: 20260218b_create_file_meta
Revises: 20260218_create_notifications
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision = '20260218b_create_file_meta'
down_revision = '20260218_create_notifications'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'file_meta'
            ) THEN
                CREATE TABLE file_meta (
                    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    contract_id UUID REFERENCES contracts(contract_id) ON DELETE SET NULL,
                    path TEXT NOT NULL,
                    sha256 VARCHAR(64),
                    file_type VARCHAR(20),
                    content_type VARCHAR(100),
                    tags TEXT[],
                    created_at TIMESTAMPTZ DEFAULT now()
                );

                CREATE INDEX IF NOT EXISTS ix_file_meta_contract_id ON file_meta(contract_id);
            END IF;
        END$$;
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS file_meta;")
