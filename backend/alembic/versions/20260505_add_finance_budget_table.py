"""add finance_budget table

Revision ID: 20260505_finance_budget
Revises: merge_cbb_af84
Create Date: 2026-05-05

Vedtatt budsjett fra økonomi-avdelingen lagres i en egen tabell
for å forhindre sammenblanding med BEFS-prediksjoner i budget-tabellen.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260505_finance_budget"
down_revision = "20260504_agresso_budgets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_budget",
        sa.Column("finance_budget_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("properties.property_id"), nullable=True),
        sa.Column("koststed_kode",       sa.String(20),         nullable=True),
        sa.Column("koststed_navn",       sa.String(200),        nullable=True),
        sa.Column("year",                sa.Integer(),          nullable=False),
        sa.Column("month",               sa.Integer(),          nullable=False),
        sa.Column("konto",               sa.String(20),         nullable=False),
        sa.Column("konto_navn",          sa.String(200),        nullable=True),
        sa.Column("category",            sa.String(50),         nullable=False),
        sa.Column("amount",              sa.Numeric(19, 4),     nullable=False),
        sa.Column("finansiering_kode",   sa.String(20),         nullable=True),
        sa.Column("prosjekt_kode",       sa.String(20),         nullable=True),
        sa.Column("is_direktorat_level", sa.Boolean(),          nullable=False, server_default="false"),
        sa.Column("import_batch_id",     sa.String(100),        nullable=True),
        sa.Column("imported_at",         sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_source",         sa.String(100),        nullable=False),
    )
    op.create_index("ix_finance_budget_year",     "finance_budget", ["year"])
    op.create_index("ix_finance_budget_property", "finance_budget", ["property_id"])
    op.create_index("ix_finance_budget_konto",    "finance_budget", ["konto"])
    op.create_index("ix_finance_budget_koststed", "finance_budget", ["koststed_kode"])
    op.create_index("ix_finance_budget_source",   "finance_budget", ["data_source"])


def downgrade() -> None:
    op.drop_index("ix_finance_budget_source",   "finance_budget")
    op.drop_index("ix_finance_budget_koststed", "finance_budget")
    op.drop_index("ix_finance_budget_konto",    "finance_budget")
    op.drop_index("ix_finance_budget_property", "finance_budget")
    op.drop_index("ix_finance_budget_year",     "finance_budget")
    op.drop_table("finance_budget")
