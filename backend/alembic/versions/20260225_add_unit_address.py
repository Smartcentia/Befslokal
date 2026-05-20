"""Add address column to units (avdelinger)

Revision ID: 20260225_unit_address
Revises: 20260224_parent_unit_id
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa

revision = "20260225_unit_address"
down_revision = "20260224_parent_unit_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("units", sa.Column("address", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("units", "address")
