"""add_query_logs_table

Revision ID: d45357f18c33
Revises: dc3106402217
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'd45357f18c33'
down_revision = 'dc3106402217'
branch_labels = None
depends_on = None


def upgrade():
    """Create query_logs table for logging SQL query generation and execution."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'query_logs' not in existing_tables:
        op.create_table(
            'query_logs',
            sa.Column('log_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_question', sa.Text, nullable=False),
            sa.Column('generated_sql', sa.Text),
            sa.Column('query_type', sa.String(50)),  # lookup, analysis, comparison, etc.
            sa.Column('execution_success', sa.Boolean, default=False),
            sa.Column('result_count', sa.Integer),
            sa.Column('execution_time_ms', sa.Integer),
            sa.Column('error_message', sa.Text),
            sa.Column('context_data', JSONB),  # Store query_analysis, entities, etc.
            sa.Column('timestamp', sa.DateTime(timezone=True),
                      server_default=sa.func.now()),
            sa.Column('user_id', sa.String(255)),
            sa.Column('conversation_id', sa.String(255)),
        )

        # Indexes for searching and analytics (idempotent)
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_success ON query_logs(execution_success)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_query_type ON query_logs(query_type)")


def downgrade():
    """Drop query_logs table."""
    op.drop_index('idx_query_logs_query_type', 'query_logs')
    op.drop_index('idx_query_logs_success', 'query_logs')
    op.drop_index('idx_query_logs_timestamp', 'query_logs')
    op.drop_table('query_logs')
