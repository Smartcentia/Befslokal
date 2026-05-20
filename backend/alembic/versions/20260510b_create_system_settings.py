"""create system_settings table

Revision ID: 20260510b_create_system_settings
Revises: 20260510_add_14_new_property_columns
Create Date: 2026-05-10
"""
from alembic import op
import sqlalchemy as sa

revision = '20260510b_create_system_settings'
down_revision = '20260510_add_14_new_property_columns'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.String(500), nullable=False),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    # Seed default: økonomidata synlig for alle
    op.execute(
        "INSERT INTO system_settings (key, value, updated_by, updated_at) "
        "VALUES ('hide_financials', 'false', 'system', NOW()) "
        "ON CONFLICT (key) DO NOTHING"
    )


def downgrade():
    op.drop_table('system_settings')
