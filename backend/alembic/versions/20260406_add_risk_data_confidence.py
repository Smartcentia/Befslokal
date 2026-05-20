"""add data_confidence, data_issues, assessment_status to risk_assessments

Revision ID: 20260406_risk_confidence
Revises: 20260327_gl_kategori_kolonner
Create Date: 2026-04-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260406_risk_confidence'
down_revision = '20260327_gl_kategori'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('risk_assessments',
        sa.Column('data_confidence', sa.Float(), nullable=True))
    op.add_column('risk_assessments',
        sa.Column('data_issues', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('risk_assessments',
        sa.Column('assessment_status', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('risk_assessments', 'assessment_status')
    op.drop_column('risk_assessments', 'data_issues')
    op.drop_column('risk_assessments', 'data_confidence')
