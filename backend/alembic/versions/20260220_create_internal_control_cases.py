"""Create the internal_control_cases table

Revision ID: 20260220_internal_control_cases
Revises: 20260217_fix_users_schema
Create Date: 2026-02-20

"""
from alembic import op
from sqlalchemy import text


revision = '20260220_internal_control_cases'
down_revision = '20260217_fix_users_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name = 'internal_control_cases'
            ) THEN
                CREATE TABLE internal_control_cases (
                    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
                    risk_assessment_id UUID REFERENCES risk_assessments(assessment_id),
                    assigned_user_id UUID REFERENCES users(user_id),
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    case_type VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'open',
                    priority VARCHAR DEFAULT 'medium',
                    due_date TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    notes VARCHAR,
                    process_state VARCHAR DEFAULT 'Opprettet',
                    process_data JSON DEFAULT '{}'::json,
                    process_history JSON DEFAULT '[]'::json,
                    follow_up_status VARCHAR DEFAULT 'none',
                    last_reminder_at TIMESTAMP WITH TIME ZONE,
                    escalated_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX ix_internal_control_cases_property_id ON internal_control_cases(property_id);
                CREATE INDEX ix_internal_control_cases_assigned_user_id ON internal_control_cases(assigned_user_id);
                CREATE INDEX ix_internal_control_cases_status ON internal_control_cases(status);
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name = 'internal_control_cases'
            ) THEN
                DROP INDEX IF EXISTS ix_internal_control_cases_property_id;
                DROP INDEX IF EXISTS ix_internal_control_cases_assigned_user_id;
                DROP INDEX IF EXISTS ix_internal_control_cases_status;
                DROP TABLE internal_control_cases;
            END IF;
        END
        $$;
    """))