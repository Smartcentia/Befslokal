"""phase 1 schema expansion

Revision ID: 9f8a7b6c5d4e
Revises: knowme-backend--0000298 (placeholder - actually should be the previous head)
Create Date: 2026-01-15 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9f8a7b6c5d4e'
down_revision = 'scheduled_activities_2026_01_10'
branch_labels = None
depends_on = None

def upgrade():
    # Idempotent: ADD COLUMN IF NOT EXISTS so re-runs (e.g. Render redeploy) never fail with DuplicateColumnError.
    # Inspector-based check can be unreliable in some deploy environments.
    op.execute("""
        ALTER TABLE properties
        ADD COLUMN IF NOT EXISTS land_area DOUBLE PRECISION,
        ADD COLUMN IF NOT EXISTS owner_name VARCHAR,
        ADD COLUMN IF NOT EXISTS org_number VARCHAR,
        ADD COLUMN IF NOT EXISTS regulation_type VARCHAR,
        ADD COLUMN IF NOT EXISTS project_phase VARCHAR,
        ADD COLUMN IF NOT EXISTS project_comments VARCHAR,
        ADD COLUMN IF NOT EXISTS full_address JSONB
    """)
    op.execute("""
        ALTER TABLE contracts
        ADD COLUMN IF NOT EXISTS has_option BOOLEAN,
        ADD COLUMN IF NOT EXISTS option_deadline DATE,
        ADD COLUMN IF NOT EXISTS option_count_total INTEGER,
        ADD COLUMN IF NOT EXISTS option_count_used INTEGER
    """)


def downgrade():
    # contracts
    op.drop_column('contracts', 'option_count_used')
    op.drop_column('contracts', 'option_count_total')
    op.drop_column('contracts', 'option_deadline')
    op.drop_column('contracts', 'has_option')

    # properties
    op.drop_column('properties', 'full_address')
    op.drop_column('properties', 'project_comments')
    op.drop_column('properties', 'project_phase')
    op.drop_column('properties', 'regulation_type')
    op.drop_column('properties', 'org_number')
    op.drop_column('properties', 'owner_name')
    op.drop_column('properties', 'land_area')
