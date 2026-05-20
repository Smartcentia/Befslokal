"""stub: 20260510d_create_meldinger — was applied locally but never committed

Revision ID: 20260510d_create_meldinger
Revises: 20260510c_create_behovsmeldinger
Create Date: 2026-05-10

"""
from alembic import op

revision = "20260510d_create_meldinger"
down_revision = "20260510c_create_behovsmeldinger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration was already applied directly to the DB.
    # Stub only — no-op.
    pass


def downgrade() -> None:
    pass
