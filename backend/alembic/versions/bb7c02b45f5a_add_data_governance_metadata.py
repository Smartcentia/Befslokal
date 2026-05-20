"""add_data_governance_metadata

Revision ID: bb7c02b45f5a
Revises: 20260207_knowledge_graph
Create Date: 2026-02-07 10:21:25.118384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bb7c02b45f5a'
down_revision: Union[str, Sequence[str], None] = '20260207_knowledge_graph'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('data_field_metadata',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('table_name', sa.String(), nullable=False),
    sa.Column('column_name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('classification_override', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # Idempotent indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_data_field_metadata_column_name ON data_field_metadata(column_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_data_field_metadata_id ON data_field_metadata(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_data_field_metadata_table_name ON data_field_metadata(table_name)")


def downgrade() -> None:
    op.drop_index(op.f('ix_data_field_metadata_table_name'), table_name='data_field_metadata')
    op.drop_index(op.f('ix_data_field_metadata_id'), table_name='data_field_metadata')
    op.drop_index(op.f('ix_data_field_metadata_column_name'), table_name='data_field_metadata')
    op.drop_table('data_field_metadata')
