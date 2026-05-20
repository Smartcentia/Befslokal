"""add_learning_loop_columns

Revision ID: b41edf14a7be
Revises: 20260203_is_active
Create Date: 2026-02-04 00:24:23.644160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b41edf14a7be'
down_revision: Union[str, Sequence[str], None] = '20260203_is_active'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add learning loop columns to query_logs table."""
    # Add new columns to query_logs
    op.add_column('query_logs', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.add_column('query_logs', sa.Column('model_used', sa.String(50), nullable=True))
    op.add_column('query_logs', sa.Column('cache_hit', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('query_logs', sa.Column('retry_count', sa.Integer(), server_default=sa.text('0'), nullable=False))
    op.add_column('query_logs', sa.Column('parent_log_id', sa.UUID(), nullable=True))

    # Add foreign key for retry tracking
    # Idempotent foreign key creation
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                    AND tc.table_name = 'query_logs'
                    AND tc.constraint_name = 'fk_query_logs_parent'
            ) THEN
                ALTER TABLE public.query_logs
                    ADD CONSTRAINT fk_query_logs_parent
                    FOREIGN KEY (parent_log_id) REFERENCES public.query_logs(log_id)
                    ON DELETE SET NULL;
            END IF;
        END
        $$;
        """
    )

    # Add indexes for performance (idempotent)
    op.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_confidence ON query_logs(confidence_score)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_model ON query_logs(model_used)")


def downgrade() -> None:
    """Remove learning loop columns from query_logs table."""
    # Drop indexes
    op.drop_index('idx_query_logs_model', table_name='query_logs')
    op.drop_index('idx_query_logs_confidence', table_name='query_logs')

    # Drop foreign key
    op.drop_constraint('fk_query_logs_parent', 'query_logs', type_='foreignkey')

    # Drop columns
    op.drop_column('query_logs', 'parent_log_id')
    op.drop_column('query_logs', 'retry_count')
    op.drop_column('query_logs', 'cache_hit')
    op.drop_column('query_logs', 'model_used')
    op.drop_column('query_logs', 'confidence_score')
