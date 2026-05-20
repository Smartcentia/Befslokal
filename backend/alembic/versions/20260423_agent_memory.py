"""create agent_memory table

Revision ID: 20260423_agent_memory
Revises: 20260423_lokasjoner
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "20260423_agent_memory"
down_revision = "20260423_lokasjoner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS agent_memory (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content     TEXT NOT NULL,
            additional_metadata JSONB DEFAULT '{}',
            embedding   vector(1536),
            created_at  TIMESTAMPTZ DEFAULT now()
        )
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS agent_memory"))
