"""Add Lydia enrichment fields: leased_area, notice_period, lokasjon_type to contracts + properties

Revision ID: 20260508_lydia_enrich
Revises: f98b219a34e8
Create Date: 2026-05-08

Strategi: Kun ADD COLUMN IF NOT EXISTS — aldri dropp eller modifiser eksisterende kolonner.
"""
from alembic import op
import sqlalchemy as sa

revision = '20260508_lydia_enrich'
down_revision = 'f98b219a34e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Contracts: nye felter fra Lydia ──────────────────────────────────────
    op.execute("""
        ALTER TABLE contracts
          ADD COLUMN IF NOT EXISTS leased_area        FLOAT,
          ADD COLUMN IF NOT EXISTS total_leased_area  FLOAT,
          ADD COLUMN IF NOT EXISTS notice_period      VARCHAR(50),
          ADD COLUMN IF NOT EXISTS option_years_text  VARCHAR(100),
          ADD COLUMN IF NOT EXISTS lydia_id           VARCHAR(20),
          ADD COLUMN IF NOT EXISTS saksnummer_lydia   VARCHAR(100),
          ADD COLUMN IF NOT EXISTS avtalenummer_lydia VARCHAR(50)
    """)

    # ── Properties: nye felter fra Lydia ─────────────────────────────────────
    op.execute("""
        ALTER TABLE properties
          ADD COLUMN IF NOT EXISTS lokasjon_type  VARCHAR(50),
          ADD COLUMN IF NOT EXISTS formaalsbygg   VARCHAR(100),
          ADD COLUMN IF NOT EXISTS lydia_id       VARCHAR(20)
    """)
    # Merk: gnr, bnr, municipality_code finnes allerede i properties


def downgrade() -> None:
    # Fjern kun de nye kolonnene — aldri data som var der fra før
    op.execute("""
        ALTER TABLE contracts
          DROP COLUMN IF EXISTS leased_area,
          DROP COLUMN IF EXISTS total_leased_area,
          DROP COLUMN IF EXISTS notice_period,
          DROP COLUMN IF EXISTS option_years_text,
          DROP COLUMN IF EXISTS lydia_id,
          DROP COLUMN IF EXISTS saksnummer_lydia,
          DROP COLUMN IF EXISTS avtalenummer_lydia
    """)
    op.execute("""
        ALTER TABLE properties
          DROP COLUMN IF EXISTS lokasjon_type,
          DROP COLUMN IF EXISTS formaalsbygg,
          DROP COLUMN IF EXISTS lydia_id
    """)
