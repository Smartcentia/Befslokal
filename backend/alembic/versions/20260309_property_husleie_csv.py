"""Add property_husleie_csv table for Innkjøpsanalyse husleie

Revision ID: 20260309_property_husleie_csv
Revises: 20260226_property_costs
Create Date: 2026-03-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260309_property_husleie_csv"
down_revision = "20260226_property_costs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "property_husleie_csv",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
    )
    op.create_index("ix_property_husleie_csv_property_id", "property_husleie_csv", ["property_id"], unique=False)
    op.create_index("ix_property_husleie_csv_year", "property_husleie_csv", ["year"], unique=False)
    op.create_index("ix_property_husleie_csv_property_year", "property_husleie_csv", ["property_id", "year"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_property_husleie_csv_property_year", table_name="property_husleie_csv")
    op.drop_index("ix_property_husleie_csv_year", table_name="property_husleie_csv")
    op.drop_index("ix_property_husleie_csv_property_id", table_name="property_husleie_csv")
    op.drop_table("property_husleie_csv")
