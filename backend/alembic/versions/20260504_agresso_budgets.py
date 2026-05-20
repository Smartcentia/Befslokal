"""agresso_budgets table – offisielt budsjett fra Agresso (Eivind 2026-04-30)

Revision ID: 20260504_agresso_budgets
Revises: 20260423_agent_memory
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260504_agresso_budgets"
down_revision = "20260423_agent_memory"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agresso_budgets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("konto", sa.String(10), nullable=False),
        sa.Column("konto_navn", sa.String(200), nullable=True),
        sa.Column("koststed_kode", sa.String(20), nullable=True),
        sa.Column("koststed_navn", sa.String(200), nullable=True),
        sa.Column("prosjekt_kode", sa.String(20), nullable=True),
        sa.Column("prosjekt_navn", sa.String(200), nullable=True),
        sa.Column("finansiering_kode", sa.String(20), nullable=True),
        sa.Column("finansiering_navn", sa.String(200), nullable=True),
        sa.Column("periode", sa.String(6), nullable=False),
        sa.Column("ar", sa.Integer, nullable=True),
        sa.Column("maaned", sa.Integer, nullable=True),
        sa.Column("belop_da", sa.Numeric(19, 4), nullable=True),
        sa.Column("kontantbelop", sa.Numeric(19, 4), nullable=True),
        sa.Column("srs_kategori", sa.String(20), nullable=True),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.property_id", ondelete="SET NULL"), nullable=True),
        sa.Column("batch_id", sa.String(100), nullable=True),
        sa.Column("imported_by", sa.String(100), nullable=True),
        sa.Column("source_file_ref", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agresso_budgets_konto", "agresso_budgets", ["konto"])
    op.create_index("ix_agresso_budgets_koststed", "agresso_budgets", ["koststed_kode"])
    op.create_index("ix_agresso_budgets_ar", "agresso_budgets", ["ar"])
    op.create_index("ix_agresso_budgets_srs", "agresso_budgets", ["srs_kategori"])
    op.create_index("ix_agresso_budgets_property", "agresso_budgets", ["property_id"])
    op.create_index("ix_agresso_budgets_batch", "agresso_budgets", ["batch_id"])


def downgrade():
    op.drop_table("agresso_budgets")
