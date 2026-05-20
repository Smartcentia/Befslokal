"""Add husleie_2026 and husleie_2026_kpi_note to properties (KPI-justert husleie Alternativ A)

Revision ID: 20260511_husleie_2026
Revises: 20260509b_gl_rent
Create Date: 2026-05-11

husleie_2026          = KPI-justert husleie 2026, beregnet fra SSB KPI index (Alternativ A)
husleie_2026_kpi_note = tekst-notat med KPI-økning og reguleringsgrad, f.eks. "+24.2% (KPI*100%)"

Disse er beregnet verdier og skal ALDRI overskrives av finance_budget eller gl_rent_2025.
"""
from alembic import op
import sqlalchemy as sa

revision = '20260511_husleie_2026'
down_revision = '20260509b_gl_rent'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('properties', sa.Column('husleie_2026', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('husleie_2026_kpi_note', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('properties', 'husleie_2026_kpi_note')
    op.drop_column('properties', 'husleie_2026')
