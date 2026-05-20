
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260207_knowledge_graph'
down_revision = '55a04487c7b3'

def upgrade():
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Table for Entities (Nodes)
    # NOTE: The 'embedding' vector column is intentionally omitted here.
    # pgvector may not be installed on all PostgreSQL hosts (e.g. Railway).
    # Add the column manually later: ALTER TABLE graph_entities ADD COLUMN embedding vector(1536);
    if 'graph_entities' not in existing_tables:
        op.create_table(
            'graph_entities',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('label', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_graph_entities_name ON graph_entities(name)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_graph_entities_label ON graph_entities(label)"))

    # 2. Table for Relationships (Edges) - only create if graph_entities exists
    if 'graph_relationships' not in existing_tables and 'graph_entities' in inspector.get_table_names():
        op.create_table(
            'graph_relationships',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('graph_entities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('target_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('graph_entities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('relation_type', sa.String(), nullable=False), # e.g., WORKS_AT, COMPLIES_WITH
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        )

    # Create indexes only if table exists
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'graph_relationships'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_graph_relationships_type ON graph_relationships(relation_type);
                CREATE INDEX IF NOT EXISTS ix_graph_relationships_source ON graph_relationships(source_id);
                CREATE INDEX IF NOT EXISTS ix_graph_relationships_target ON graph_relationships(target_id);
            END IF;
        END $$;
    """))

def downgrade():
    op.drop_table('graph_relationships')
    op.drop_table('graph_entities')
