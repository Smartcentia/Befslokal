"""create befs_budsjett_sammenligning table

Revision ID: 20260512_befs_budsjett_sammenligning
Revises: 20260511_deviation_images, 20260511_husleie_2026
Create Date: 2026-05-12

Staging table for økonomiavdelingens autoriserte CSV (budsjettt2026ver04).
Populated by: backend/app/scripts/import_budsjett_sammenligning.py
"""
from alembic import op
import sqlalchemy as sa

revision = "20260512_befs_budsjett_sammenligning"
down_revision = ("20260511_deviation_images", "20260511_husleie_2026")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS befs_budsjett_sammenligning (
            id               SERIAL PRIMARY KEY,
            eiendom          TEXT NOT NULL,
            region           TEXT,
            regn_2025_ok     NUMERIC,
            befs_pred_2026   NUMERIC,
            budsjett_2026_ok NUMERIC,
            merknad          TEXT,
            import_batch_id  TEXT,
            created_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_befs_budsjett_region
        ON befs_budsjett_sammenligning (region)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS befs_budsjett_sammenligning")
