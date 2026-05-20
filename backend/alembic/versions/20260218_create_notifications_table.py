"""Create notifications table

Revision ID: 20260218_create_notifications
Revises: 20260217b_fix_core_tables
Create Date: 2026-02-18
"""
from alembic import op
from sqlalchemy import text

revision = '20260218_create_notifications'
down_revision = '20260217b_fix_core_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'notifications'
            ) THEN
                CREATE TABLE notifications (
                    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    message VARCHAR NOT NULL,
                    notification_type VARCHAR DEFAULT 'internal_control',
                    related_entity_type VARCHAR,
                    related_entity_id UUID,
                    is_read BOOLEAN DEFAULT FALSE,
                    read_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX ix_notifications_user_id ON notifications(user_id);
                CREATE INDEX ix_notifications_is_read ON notifications(user_id, is_read);
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        DROP TABLE IF EXISTS notifications;
    """))
