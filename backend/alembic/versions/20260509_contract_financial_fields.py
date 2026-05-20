"""Add contract financial fields and malgruppe from eiendomsoversikt CSV

Revision ID: 20260509_contract_fin
Revises: 20260508_merge2
Create Date: 2026-05-09

Strategi: ADD COLUMN IF NOT EXISTS — aldri dropp eller modifiser eksisterende kolonner.
Felter:
  properties.malgruppe             ← Målgruppe (Akutt/Omsorg/EMA/BFS/FVK/Kontor)
  properties.contract_rent_nok     ← Kontraktsleie kr/år (fra leieavtale, ikke GL)
  properties.contract_maint_nok    ← Indre vedlikehold kr/år
  properties.contract_common_nok   ← Felleskostnader kr/år
  properties.contract_user_ops_nok ← Brukeravhengige driftskostnader kr/år
  properties.extension_terms       ← Adgang til forlengelse og vilkår (tekst)
  properties.price_adj_clause      ← Årlig prisjusteringsfaktaktor (tekst)
"""
from alembic import op

revision = '20260509_contract_fin'
down_revision = '20260508_merge2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE properties
          ADD COLUMN IF NOT EXISTS malgruppe              VARCHAR(100),
          ADD COLUMN IF NOT EXISTS contract_rent_nok      NUMERIC(14,2),
          ADD COLUMN IF NOT EXISTS contract_maint_nok     NUMERIC(14,2),
          ADD COLUMN IF NOT EXISTS contract_common_nok    NUMERIC(14,2),
          ADD COLUMN IF NOT EXISTS contract_user_ops_nok  NUMERIC(14,2),
          ADD COLUMN IF NOT EXISTS extension_terms        VARCHAR(500),
          ADD COLUMN IF NOT EXISTS price_adj_clause       VARCHAR(300)
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_prop_malgruppe ON properties (malgruppe)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_prop_malgruppe")
    op.execute("""
        ALTER TABLE properties
          DROP COLUMN IF EXISTS malgruppe,
          DROP COLUMN IF EXISTS contract_rent_nok,
          DROP COLUMN IF EXISTS contract_maint_nok,
          DROP COLUMN IF EXISTS contract_common_nok,
          DROP COLUMN IF EXISTS contract_user_ops_nok,
          DROP COLUMN IF EXISTS extension_terms,
          DROP COLUMN IF EXISTS price_adj_clause
    """)
