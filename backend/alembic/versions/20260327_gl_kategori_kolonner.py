"""gl_transactions: legg til innkjopskategori og underkategori kolonner

Revision ID: 20260327_gl_kategori
Revises: 20260320_srs_regnskap_fase1
Create Date: 2026-03-27

Bakgrunn:
  Agresso-eksporter fra 2025+ inneholder fire nye kolonner som ikke var
  fanget opp i tidligere import:
    - Innkjøpskategorier     → innkjopskategori_kode (VARCHAR 20)
    - Innkjøpskategorier(T)  → innkjopskategori_navn (VARCHAR 200)
    - Underkategorier        → underkategori_kode (VARCHAR 20)
    - Underkategorier(T)     → underkategori_navn (VARCHAR 200)

  Alle er nullable — eksisterende rader forblir urørt (immutabilitetsregel).
"""
from alembic import op
import sqlalchemy as sa

revision = "20260327_gl_kategori"
down_revision = "20260320_srs_fase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "gl_transactions",
        sa.Column("innkjopskategori_kode", sa.String(20), nullable=True),
    )
    op.add_column(
        "gl_transactions",
        sa.Column("innkjopskategori_navn", sa.String(200), nullable=True),
    )
    op.add_column(
        "gl_transactions",
        sa.Column("underkategori_kode", sa.String(20), nullable=True),
    )
    op.add_column(
        "gl_transactions",
        sa.Column("underkategori_navn", sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gl_transactions", "underkategori_navn")
    op.drop_column("gl_transactions", "underkategori_kode")
    op.drop_column("gl_transactions", "innkjopskategori_navn")
    op.drop_column("gl_transactions", "innkjopskategori_kode")
