"""create budget table

Revision ID: 20260219_create_budget_table
Revises: 20260218d_add_contract_cols
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20260219_create_budget_table'
down_revision = '20260218d_add_contract_cols'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'budget',
        sa.Column('budget_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('property_id', UUID(as_uuid=True), sa.ForeignKey('properties.property_id'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('is_synthetic', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('data_source', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table('budget')
