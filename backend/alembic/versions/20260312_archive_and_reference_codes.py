"""Add archive_code (contracts) and reference_code (parties)

Revision ID: 20260312_archive_ref
Revises: 20260309_property_husleie_csv
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa

revision = "20260312_archive_ref"
down_revision = "20260309_property_husleie_csv"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column("archive_code", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_contracts_archive_code",
        "contracts",
        ["archive_code"],
        unique=True,
    )

    op.add_column(
        "parties",
        sa.Column("reference_code", sa.String(20), nullable=True),
    )
    op.create_index(
        "ix_parties_reference_code",
        "parties",
        ["reference_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_parties_reference_code", table_name="parties")
    op.drop_column("parties", "reference_code")

    op.drop_index("ix_contracts_archive_code", table_name="contracts")
    op.drop_column("contracts", "archive_code")
