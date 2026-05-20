"""Add description, area to properties and contract_name to contracts

Revision ID: 20260312_desc_area_cname
Revises: 20260312_archive_ref
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa

revision = "20260312_desc_area_cname"
down_revision = "20260312_archive_ref"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("description", sa.String(), nullable=True),
    )
    op.add_column(
        "properties",
        sa.Column("area", sa.String(), nullable=True),
    )
    op.add_column(
        "contracts",
        sa.Column("contract_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contracts", "contract_name")
    op.drop_column("properties", "area")
    op.drop_column("properties", "description")
