"""add pgvector

Revision ID: add_pgvector
Revises: phase_2_center_model
Create Date: 2026-01-16 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_pgvector'
down_revision = 'phase_2_center_model'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Check if pgvector is installed on this PostgreSQL instance.
    #    We check pg_available_extensions BEFORE attempting CREATE EXTENSION
    #    to avoid aborting the alembic transaction (PostgreSQL aborts the entire
    #    transaction on DDL errors, even if Python catches the exception).
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
    ))
    if not result.fetchone():
        print("WARNING: pgvector (vector) extension not available on this PostgreSQL instance. "
              "Skipping embedding column and HNSW index. "
              "Install pgvector on the server to enable semantic search.")
        return

    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # 2. Add embedding column to text_content (idempotent)
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'text_content'
        AND column_name = 'embedding'
    """))
    if not result.fetchone():
        conn.execute(sa.text(
            "ALTER TABLE text_content ADD COLUMN embedding vector(1536)"
        ))

    # 3. Create HNSW index for fast similarity search (idempotent)
    result = conn.execute(sa.text("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'text_content'
        AND indexname = 'idx_text_content_embedding'
    """))
    if not result.fetchone():
        conn.execute(sa.text("""
            CREATE INDEX idx_text_content_embedding
            ON text_content
            USING hnsw (embedding vector_l2_ops)
            WITH (m = 16, ef_construction = 64)
        """))


def downgrade():
    conn = op.get_bind()
    # Check if vector extension exists before trying to drop things
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
    ))
    if result.fetchone():
        conn.execute(sa.text(
            "DROP INDEX IF EXISTS idx_text_content_embedding"
        ))
        conn.execute(sa.text(
            "ALTER TABLE text_content DROP COLUMN IF EXISTS embedding"
        ))
        conn.execute(sa.text("DROP EXTENSION IF EXISTS vector"))
