"""Add maintenance_plans and maintenance_tasks tables

Revision ID: 20260421_maintenance_plan
Revises: 20260420_fdvu_phase1
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260421_maintenance_plan'
down_revision = '20260420_fdvu_phase1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'maintenance_plans',
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('property_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('properties.property_id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('building_components.component_id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True, server_default='preventive'),
        sa.Column('frequency_months', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('responsible_role', sa.String(50), nullable=True, server_default='janitor'),
        sa.Column('estimated_cost_nok', sa.Numeric(10, 2), nullable=True),
        sa.Column('ns3451_code', sa.String(20), nullable=True),
        sa.Column('last_performed_date', sa.Date(), nullable=True),
        sa.Column('next_due_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_maintenance_plans_property_id', 'maintenance_plans', ['property_id'])
    op.create_index('ix_maintenance_plans_next_due_date', 'maintenance_plans', ['next_due_date'])

    op.create_table(
        'maintenance_tasks',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('maintenance_plans.plan_id', ondelete='CASCADE'), nullable=False),
        sa.Column('property_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('properties.property_id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('building_components.component_id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('actual_cost_nok', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_maintenance_tasks_plan_id', 'maintenance_tasks', ['plan_id'])
    op.create_index('ix_maintenance_tasks_property_id', 'maintenance_tasks', ['property_id'])
    op.create_index('ix_maintenance_tasks_due_date', 'maintenance_tasks', ['due_date'])
    op.create_index('ix_maintenance_tasks_status', 'maintenance_tasks', ['status'])


def downgrade() -> None:
    op.drop_table('maintenance_tasks')
    op.drop_table('maintenance_plans')
