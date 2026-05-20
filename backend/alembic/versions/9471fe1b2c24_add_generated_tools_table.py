"""add_generated_tools_table

Revision ID: 9471fe1b2c24
Revises: e33b8f92c441
Create Date: 2026-01-14 11:28:49.239478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '9471fe1b2c24'
down_revision: Union[str, Sequence[str], None] = 'e33b8f92c441'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create generated_tools table."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'generated_tools' not in existing_tables:
        op.create_table(
            'generated_tools',
            sa.Column('tool_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(255), unique=True, nullable=False),
            sa.Column('description', sa.Text),
            sa.Column('python_code', sa.Text, nullable=False),
            sa.Column('sql_pattern', sa.Text),
            sa.Column('status', sa.String(50), default='pending'), # pending, active, deprecated
            sa.Column('source_log_ids', JSONB), # List of query_log IDs that inspired this
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('version', sa.Integer, default=1)
        )

        # Idempotent indexes
        op.execute("CREATE INDEX IF NOT EXISTS idx_generated_tools_status ON generated_tools(status)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_generated_tools_name ON generated_tools(name)")


def downgrade() -> None:
    """Drop generated_tools table."""
    op.drop_index('idx_generated_tools_name', 'generated_tools')
    op.drop_index('idx_generated_tools_status', 'generated_tools')
    op.drop_table('generated_tools')
