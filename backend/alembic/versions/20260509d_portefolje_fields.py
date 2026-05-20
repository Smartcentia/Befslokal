"""Add portefolje fields from Eiendomsportefolje CSV

Revision ID: 20260509d_portefolje
Revises: 20260509c_egnethet
Create Date: 2026-05-09

Felter:
  properties.lok_distrikt       ← Lok: Distrikt (f.eks. "01 - Nord")
  properties.fylke               ← Fylke (f.eks. "Trøndelag")
  properties.leased_area_kvm     ← Areal inkl fellesareal i leiekontrakt (kvm)
  properties.elements_id         ← Elements saksnummer (f.eks. "2004/10438")
  properties.utleier_kategori    ← Utleier kategori (1 = privat, 2 = offentlig)
"""
from alembic import op

revision = '20260509d_portefolje'
down_revision = '20260509c_egnethet'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE properties
          ADD COLUMN IF NOT EXISTS lok_distrikt       VARCHAR(50),
          ADD COLUMN IF NOT EXISTS fylke              VARCHAR(50),
          ADD COLUMN IF NOT EXISTS leased_area_kvm    NUMERIC(10,1),
          ADD COLUMN IF NOT EXISTS elements_id        VARCHAR(200),
          ADD COLUMN IF NOT EXISTS utleier_kategori   SMALLINT
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_prop_lok_distrikt ON properties (lok_distrikt)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_prop_fylke ON properties (fylke)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_prop_utleier_kat ON properties (utleier_kategori)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_prop_lok_distrikt")
    op.execute("DROP INDEX IF EXISTS idx_prop_fylke")
    op.execute("DROP INDEX IF EXISTS idx_prop_utleier_kat")
    op.execute("""
        ALTER TABLE properties
          DROP COLUMN IF EXISTS lok_distrikt,
          DROP COLUMN IF EXISTS fylke,
          DROP COLUMN IF EXISTS leased_area_kvm,
          DROP COLUMN IF EXISTS elements_id,
          DROP COLUMN IF EXISTS utleier_kategori
    """)
