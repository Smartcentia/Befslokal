"""add_synthetic_flag_to_financials

Revision ID: 20260210_add_syn_fin
Revises: 75cc813059f9
Create Date: 2026-02-10 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260210_add_syn_fin'
down_revision = '75cc813059f9'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    def exists(tbl: str) -> bool:
        return conn.execute(text("SELECT to_regclass(:t)"), {"t": f"public.{tbl}"}).scalar() is not None
    # Add columns to budget table
    if exists('budget'):
        op.add_column('budget', sa.Column('is_synthetic', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        op.add_column('budget', sa.Column('data_source', sa.String(length=100), nullable=True))

    # Add columns to gl_transactions table
    if exists('gl_transactions'):
        op.add_column('gl_transactions', sa.Column('is_synthetic', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        op.add_column('gl_transactions', sa.Column('data_source', sa.String(length=100), nullable=True))


def downgrade():
    conn = op.get_bind()
    def exists(tbl: str) -> bool:
        return conn.execute(text("SELECT to_regclass(:t)"), {"t": f"public.{tbl}"}).scalar() is not None
    # Remove columns from gl_transactions table
    if exists('gl_transactions'):
        op.drop_column('gl_transactions', 'data_source')
        op.drop_column('gl_transactions', 'is_synthetic')

    # Remove columns from budget table
    if exists('budget'):
        op.drop_column('budget', 'data_source')
        op.drop_column('budget', 'is_synthetic')
