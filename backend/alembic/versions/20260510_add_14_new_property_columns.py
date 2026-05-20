"""add 14 new property columns from eiendomsportefolje csv

Revision ID: 20260510_add_14_new_property_columns
Revises: f98b219a34e8
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa

revision = '20260510_add_14_new_property_columns'
down_revision = 'f98b219a34e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('tilstandsgrad', sa.String(), nullable=True))
    op.add_column('properties', sa.Column('antall_ansatte', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('p_plasser', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('eksklusivt_areal_kvm', sa.Numeric(10, 1), nullable=True))
    op.add_column('properties', sa.Column('tilleggsareal_kvm', sa.Numeric(10, 1), nullable=True))
    op.add_column('properties', sa.Column('reduksjon_addendum_kvm', sa.Numeric(10, 1), nullable=True))
    op.add_column('properties', sa.Column('energi_kr_per_ar', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('oppvarming_kr_per_ar', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('mva_kompensasjon_kr_per_ar', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('kontantinnskudd_kr', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('kpi_oppstartsdato', sa.Date(), nullable=True))
    op.add_column('properties', sa.Column('kontraktsleie_ved_oppstart_kr', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('kommunale_gebyrer_kr', sa.Numeric(14, 2), nullable=True))
    op.add_column('properties', sa.Column('kommentar', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('properties', 'kommentar')
    op.drop_column('properties', 'kommunale_gebyrer_kr')
    op.drop_column('properties', 'kontraktsleie_ved_oppstart_kr')
    op.drop_column('properties', 'kpi_oppstartsdato')
    op.drop_column('properties', 'kontantinnskudd_kr')
    op.drop_column('properties', 'mva_kompensasjon_kr_per_ar')
    op.drop_column('properties', 'oppvarming_kr_per_ar')
    op.drop_column('properties', 'energi_kr_per_ar')
    op.drop_column('properties', 'reduksjon_addendum_kvm')
    op.drop_column('properties', 'tilleggsareal_kvm')
    op.drop_column('properties', 'eksklusivt_areal_kvm')
    op.drop_column('properties', 'p_plasser')
    op.drop_column('properties', 'antall_ansatte')
    op.drop_column('properties', 'tilstandsgrad')
