"""add_monitoring_tables

Revision ID: 1dda872648d0
Revises: 003_add_risk_assessment_tables
Create Date: 2025-11-01 11:29:30.613192

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1dda872648d0'
down_revision = '003_add_risk_assessment_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_call_logs table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS api_call_logs (
            call_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service_name VARCHAR(50) NOT NULL,
            endpoint VARCHAR(200),
            request_count INTEGER NOT NULL DEFAULT 1,
            cost_estimate FLOAT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            response_time_ms INTEGER,
            status_code INTEGER,
            error_message VARCHAR(500)
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_api_call_logs_service_name ON api_call_logs(service_name)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_api_call_logs_timestamp ON api_call_logs(timestamp)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS api_call_logs CASCADE"))
