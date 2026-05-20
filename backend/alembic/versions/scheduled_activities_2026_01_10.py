"""Add scheduled activities calendar system

Revision ID: scheduled_activities_2026_01_10
Revises: 001_initial
Create Date: 2026-01-10 11:15:00

Uses raw SQL so we only reference properties (no users FK - users not in chain).
"""
from alembic import op
from sqlalchemy import text, inspect

revision = 'scheduled_activities_2026_01_10'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    existing = inspector.get_table_names()

    if 'scheduled_activities' not in existing:
        # Check if properties.property_id exists before creating FK
        has_property_id = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'properties'
                    AND column_name = 'property_id'
            )
        """)).scalar()

        if has_property_id:
            op.execute(text("""
                CREATE TABLE scheduled_activities (
                    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    activity_type VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    priority VARCHAR NOT NULL DEFAULT 'medium',
                    responsible_role VARCHAR NOT NULL,
                    assigned_user_id UUID,
                    recurrence_rule JSONB NOT NULL,
                    next_due_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    last_generated_at TIMESTAMP WITH TIME ZONE,
                    enabled BOOLEAN NOT NULL DEFAULT true,
                    property_tags_required JSONB,
                    property_tags_excluded JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    created_by VARCHAR
                )
            """))
        else:
            op.execute(text("""
                CREATE TABLE scheduled_activities (
                    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    property_id UUID NOT NULL,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    activity_type VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    priority VARCHAR NOT NULL DEFAULT 'medium',
                    responsible_role VARCHAR NOT NULL,
                    assigned_user_id UUID,
                    recurrence_rule JSONB NOT NULL,
                    next_due_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    last_generated_at TIMESTAMP WITH TIME ZONE,
                    enabled BOOLEAN NOT NULL DEFAULT true,
                    property_tags_required JSONB,
                    property_tags_excluded JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    created_by VARCHAR
                )
            """))

        op.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_activities_property ON scheduled_activities(property_id)"))
        op.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_activities_next_due ON scheduled_activities(next_due_date)"))
        op.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_activities_enabled ON scheduled_activities(enabled)"))

    if 'activity_templates' not in existing:
        op.execute(text("""
            CREATE TABLE activity_templates (
                template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR NOT NULL,
                description VARCHAR,
                category VARCHAR NOT NULL,
                priority VARCHAR NOT NULL DEFAULT 'medium',
                activity_type VARCHAR NOT NULL,
                recurrence_pattern JSONB NOT NULL,
                responsible_role VARCHAR NOT NULL,
                property_tags_required JSONB,
                property_tags_excluded JSONB,
                enabled BOOLEAN NOT NULL DEFAULT true,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))


def downgrade():
    op.execute(text("DROP INDEX IF EXISTS idx_scheduled_activities_enabled"))
    op.execute(text("DROP INDEX IF EXISTS idx_scheduled_activities_next_due"))
    op.execute(text("DROP INDEX IF EXISTS idx_scheduled_activities_property"))
    op.execute(text("DROP TABLE IF EXISTS activity_templates CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS scheduled_activities CASCADE"))
