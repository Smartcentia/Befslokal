"""add ompostering fields to gl_transactions

Revision ID: 20260413_ompostering
Revises: merge_cbb_af84
Create Date: 2026-04-13

Legger til self-referential FK + sporingsfelter for ompostering/korrigeringsbilag (H1/H2/HB/RE).
Originalbilag røres aldri — immutabilitetsprinsipp.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260413_ompostering"
down_revision = "merge_cbb_af84"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "gl_transactions",
        sa.Column("original_bilag_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "gl_transactions",
        sa.Column("ompostert_av", sa.String(100), nullable=True),
    )
    op.add_column(
        "gl_transactions",
        sa.Column("ompostert_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "gl_transactions",
        sa.Column("omposterings_kommentar", sa.String(500), nullable=True),
    )
    op.create_foreign_key(
        "fk_gl_original_bilag",
        "gl_transactions",
        "gl_transactions",
        ["original_bilag_id"],
        ["transaction_id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_gl_original_bilag", "gl_transactions", ["original_bilag_id"])


def downgrade() -> None:
    op.drop_index("ix_gl_original_bilag", table_name="gl_transactions")
    op.drop_constraint("fk_gl_original_bilag", "gl_transactions", type_="foreignkey")
    op.drop_column("gl_transactions", "omposterings_kommentar")
    op.drop_column("gl_transactions", "ompostert_at")
    op.drop_column("gl_transactions", "ompostert_av")
    op.drop_column("gl_transactions", "original_bilag_id")
