"""add infrastructure costs table

Revision ID: add_infrastructure_costs
Revises: 
Create Date: 2026-01-17 13:04:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'add_infrastructure_costs'
down_revision = '001_initial'  # Depends on initial migration
depends_on = None


def upgrade() -> None:
    # Check if table already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'infrastructure_costs' not in existing_tables:
        op.create_table(
            'infrastructure_costs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('service_name', sa.String(length=50), nullable=False),
            sa.Column('collection_date', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            
            # Raw metrics from CLI as JSON
            sa.Column('raw_metrics', JSONB, nullable=True),
            
            # Calculated costs
            sa.Column('estimated_cost_usd', sa.Numeric(10, 2), nullable=True),
            
            # Specific metrics
            sa.Column('active_time_seconds', sa.Integer(), nullable=True),
            sa.Column('cpu_used_seconds', sa.Integer(), nullable=True),
            sa.Column('storage_gb', sa.Numeric(10, 2), nullable=True),
            sa.Column('bandwidth_gb', sa.Numeric(10, 2), nullable=True),
            
            # Metadata
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for efficient querying
        op.create_index(
            'idx_costs_service_date',
            'infrastructure_costs',
            ['service_name', 'collection_date']
        )
        
        op.create_index(
            'idx_costs_collection_date',
            'infrastructure_costs',
            ['collection_date']
        )


def downgrade() -> None:
    op.drop_index('idx_costs_collection_date', table_name='infrastructure_costs')
    op.drop_index('idx_costs_service_date', table_name='infrastructure_costs')
    op.drop_table('infrastructure_costs')
