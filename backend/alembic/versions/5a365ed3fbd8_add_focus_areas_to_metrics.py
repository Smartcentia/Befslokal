"""add focus areas to metrics

Revision ID: 5a365ed3fbd8
Revises: 9471fe1b2c24
Create Date: 2026-01-14 17:16:21.662577

Creates dashboard_metrics if missing, then adds columns.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = '5a365ed3fbd8'
down_revision: Union[str, Sequence[str], None] = '9471fe1b2c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure dashboard_metrics table exists (not created in any prior migration)
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS dashboard_metrics (
            metric_id SERIAL PRIMARY KEY,
            properties_count INTEGER DEFAULT 0,
            contracts_count INTEGER DEFAULT 0,
            risks_count INTEGER DEFAULT 0,
            total_annual_rent FLOAT DEFAULT 0,
            total_maintenance_cost FLOAT DEFAULT 0,
            last_updated TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    # 2. Add new columns (IF NOT EXISTS not supported in PostgreSQL for ADD COLUMN; use DO block)
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dashboard_metrics' AND column_name = 'critical_deviations') THEN
                ALTER TABLE dashboard_metrics ADD COLUMN critical_deviations INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dashboard_metrics' AND column_name = 'expiring_contracts') THEN
                ALTER TABLE dashboard_metrics ADD COLUMN expiring_contracts INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dashboard_metrics' AND column_name = 'overdue_tasks') THEN
                ALTER TABLE dashboard_metrics ADD COLUMN overdue_tasks INTEGER DEFAULT 0;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(text("ALTER TABLE dashboard_metrics DROP COLUMN IF EXISTS overdue_tasks"))
    op.execute(text("ALTER TABLE dashboard_metrics DROP COLUMN IF EXISTS expiring_contracts"))
    op.execute(text("ALTER TABLE dashboard_metrics DROP COLUMN IF EXISTS critical_deviations"))
