"""Add batch_jobs table

Revision ID: a1b2c3d4e5f6
Revises: 75cc813059f9
Create Date: 2025-11-10 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '75cc813059f9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            progress INTEGER NOT NULL DEFAULT 0,
            total_items INTEGER NOT NULL DEFAULT 0,
            processed_items INTEGER NOT NULL DEFAULT 0,
            success_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            config JSONB NOT NULL,
            property_ids JSONB,
            results JSONB,
            errors JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            error_message VARCHAR(1000),
            error_details JSONB,
            worker_id VARCHAR(100),
            CONSTRAINT check_batch_job_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
            CONSTRAINT check_batch_job_progress CHECK (progress >= 0 AND progress <= 100)
        )
    """))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_jobs_status ON batch_jobs(status)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_jobs_job_type ON batch_jobs(job_type)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_jobs_created_at ON batch_jobs(created_at)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_batch_jobs_worker_id ON batch_jobs(worker_id)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS batch_jobs CASCADE"))
