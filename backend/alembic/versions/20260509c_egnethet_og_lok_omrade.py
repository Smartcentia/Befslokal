"""Add egnethet, prioritet og lok_omrade fields from eiendomsoversikt CSV

Revision ID: 20260509c_egnethet
Revises: 20260509b_gl_rent
Create Date: 2026-05-09

Felter:
  properties.lok_omrade              ← Lok: Område (f.eks. "03 - Trøndelag") — HAR DATA NÅ
  properties.egnethet_lokalisering   ← Egnethet lokalisering (fremtidig data)
  properties.egnethet_bygg           ← Egnethet bygg (fremtidig data)
  properties.prioritert_videroforing ← Prioritert viderført/utviklet (fremtidig data)
  properties.ar_videreutvikling      ← År for videreutvikling (fremtidig data)
  properties.kostnader_videreutvikling ← Kostnader til videreutvikling kr (fremtidig data)
"""
from alembic import op

revision = '20260509c_egnethet'
down_revision = '20260509b_gl_rent'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE properties
          ADD COLUMN IF NOT EXISTS lok_omrade                VARCHAR(50),
          ADD COLUMN IF NOT EXISTS egnethet_lokalisering     VARCHAR(100),
          ADD COLUMN IF NOT EXISTS egnethet_bygg             VARCHAR(100),
          ADD COLUMN IF NOT EXISTS prioritert_videroforing   VARCHAR(50),
          ADD COLUMN IF NOT EXISTS ar_videreutvikling        INTEGER,
          ADD COLUMN IF NOT EXISTS kostnader_videreutvikling NUMERIC(14,2)
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_prop_lok_omrade ON properties (lok_omrade)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_prop_egnethet_bygg ON properties (egnethet_bygg)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_prop_lok_omrade")
    op.execute("DROP INDEX IF EXISTS idx_prop_egnethet_bygg")
    op.execute("""
        ALTER TABLE properties
          DROP COLUMN IF EXISTS lok_omrade,
          DROP COLUMN IF EXISTS egnethet_lokalisering,
          DROP COLUMN IF EXISTS egnethet_bygg,
          DROP COLUMN IF EXISTS prioritert_videroforing,
          DROP COLUMN IF EXISTS ar_videreutvikling,
          DROP COLUMN IF EXISTS kostnader_videreutvikling
    """)
