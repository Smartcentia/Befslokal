"""add_performance_indexes

Revision ID: d4e9de624aec
Revises: 1dda872648d0
Create Date: 2025-11-01 11:36:34.183860

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e9de624aec'
down_revision = '1dda872648d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add performance indexes - each in separate execute for asyncpg compatibility
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_proximity_services_expires_at ON proximity_services(expires_at)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_proximity_services_property_expires ON proximity_services(property_id, expires_at)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_risk_assessments_property_date ON risk_assessments(property_id, assessment_date DESC)"))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_proximity_services_property_expires"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_proximity_services_expires_at"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_risk_assessments_property_date"))
