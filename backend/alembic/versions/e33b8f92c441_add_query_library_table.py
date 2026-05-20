"""add_query_library_table

Revision ID: e33b8f92c441
Revises: d45357f18c33
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e33b8f92c441'
down_revision = 'd45357f18c33'
branch_labels = None
depends_on = None


def upgrade():
    """Create query_library table for storing reusable query patterns."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'query_library' not in existing_tables:
        op.create_table(
            'query_library',
            sa.Column('query_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('query_name', sa.String(255), unique=True, nullable=False,
                      comment='Descriptive name generated from SQL pattern'),
            sa.Column('user_question_pattern', sa.Text, nullable=False,
                      comment='Example user question that this query answers'),
            sa.Column('sql_template', sa.Text, nullable=False,
                      comment='The SQL query template'),
            sa.Column('description', sa.Text,
                      comment='Auto-generated description of what this query does'),
            sa.Column('usage_count', sa.Integer, default=0, nullable=False,
                      comment='Number of times this query has been used'),
            sa.Column('success_rate', sa.Float, default=1.0, nullable=False,
                      comment='Success rate (0.0-1.0) of query executions'),
            sa.Column('avg_execution_time_ms', sa.Integer,
                      comment='Average execution time in milliseconds'),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True),
                      onupdate=sa.func.now()),
            sa.Column('created_by', sa.String(50), default='auto', nullable=False,
                      comment='auto (system-generated) or manual (human-created)'),
        )

        # Indexes for query library (idempotent)
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_library_usage ON query_library(usage_count)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_library_success ON query_library(success_rate)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_library_created ON query_library(created_at)")

        # Full-text search index for user_question_pattern (for similarity matching)
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_library_question_search ON query_library USING gin(to_tsvector('norwegian', user_question_pattern))")


def downgrade():
    """Drop query_library table."""
    op.drop_index('idx_query_library_question_search', 'query_library')
    op.drop_index('idx_query_library_created', 'query_library')
    op.drop_index('idx_query_library_success', 'query_library')
    op.drop_index('idx_query_library_usage', 'query_library')
    op.drop_table('query_library')
