"""add case_id and original_filename to file_meta for deviation images

Revision ID: 20260511_deviation_images
Revises: f98b219a34e8
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa

revision = "20260511_deviation_images"
down_revision = ("f98b219a34e8", "20260510d_create_meldinger", "add_eierskap_data_kilde_inst")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "file_meta",
        sa.Column("case_id", sa.UUID(as_uuid=True), sa.ForeignKey("internal_control_cases.case_id"), nullable=True),
    )
    op.add_column(
        "file_meta",
        sa.Column("original_filename", sa.String(), nullable=True),
    )
    op.create_index("ix_file_meta_case_id", "file_meta", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_file_meta_case_id", table_name="file_meta")
    op.drop_column("file_meta", "original_filename")
    op.drop_column("file_meta", "case_id")
