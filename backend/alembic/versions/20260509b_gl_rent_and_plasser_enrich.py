"""Add gl_rent_2025 (faktisk husleie fra GL) and enrich plasser/dept from institution_plasser

Revision ID: 20260509b_gl_rent
Revises: 20260509_contract_fin
Create Date: 2026-05-09

Arkitektur husleie:
  contract_rent_nok  = avtalefestet husleie fra leieavtale (CSV-kilde)
  gl_rent_2025       = faktisk husleie 2025 fra GL-regnskap (srs_kategori='Lokaler')

Disse er to ulike ting og skal ALDRI overskrives med hverandres verdier.
"""
from alembic import op

revision = '20260509b_gl_rent'
down_revision = '20260509_contract_fin'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ny kolonne: faktisk husleie fra GL 2025
    op.execute("""
        ALTER TABLE properties
          ADD COLUMN IF NOT EXISTS gl_rent_2025 NUMERIC(14,2)
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_prop_gl_rent_2025 ON properties (gl_rent_2025)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_prop_gl_rent_2025")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS gl_rent_2025")
