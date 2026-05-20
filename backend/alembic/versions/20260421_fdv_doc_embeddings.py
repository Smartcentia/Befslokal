"""FDV document embeddings and text extraction columns

Revision ID: 20260421_fdv_doc_embeddings
Revises: 20260421_building_structure
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = '20260421_fdv_doc_embeddings'
down_revision = '20260421_building_structure'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("fdv_documents")}

    if "extracted_text" not in existing_cols:
        op.add_column("fdv_documents", sa.Column("extracted_text", sa.Text(), nullable=True))

    if "extraction_status" not in existing_cols:
        op.add_column(
            "fdv_documents",
            sa.Column(
                "extraction_status",
                sa.String(30),
                nullable=False,
                server_default="pending",
            ),
        )

    if "page_count" not in existing_cols:
        op.add_column("fdv_documents", sa.Column("page_count", sa.Integer(), nullable=True))

    # pgvector: use raw SQL since Alembic doesn't know the vector type
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE fdv_documents ADD COLUMN IF NOT EXISTS embedding vector(1536)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fdv_documents_embedding "
        "ON fdv_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_fdv_documents_embedding")
    op.execute("ALTER TABLE fdv_documents DROP COLUMN IF EXISTS embedding")

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("fdv_documents")}

    if "page_count" in existing_cols:
        op.drop_column("fdv_documents", "page_count")
    if "extraction_status" in existing_cols:
        op.drop_column("fdv_documents", "extraction_status")
    if "extracted_text" in existing_cols:
        op.drop_column("fdv_documents", "extracted_text")
