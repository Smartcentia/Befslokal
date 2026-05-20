"""add_master_data_crosswalk

Revision ID: 8be2957122b1
Revises: f98b219a34e8
Create Date: 2026-02-22 18:21:55.205797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8be2957122b1'
down_revision: Union[str, Sequence[str], None] = 'f98b219a34e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    if conn.dialect.has_table(conn, 'master_data_crosswalk'):
        return
    op.create_table(
        'master_data_crosswalk',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('collision_flag', sa.Boolean(), nullable=True),
        sa.Column('match_method', sa.String(length=50), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=True),
        sa.Column('run_id', sa.String(length=50), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('audit_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_master_data_crosswalk_id'), 'master_data_crosswalk', ['id'], unique=False)
    op.create_index(op.f('ix_master_data_crosswalk_relation_type'), 'master_data_crosswalk', ['relation_type'], unique=False)
    op.create_index(op.f('ix_master_data_crosswalk_source_id'), 'master_data_crosswalk', ['source_id'], unique=False)
    op.create_index(op.f('ix_master_data_crosswalk_source_type'), 'master_data_crosswalk', ['source_type'], unique=False)
    op.create_index(op.f('ix_master_data_crosswalk_target_id'), 'master_data_crosswalk', ['target_id'], unique=False)
    op.create_index(op.f('ix_master_data_crosswalk_target_type'), 'master_data_crosswalk', ['target_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_master_data_crosswalk_target_type'), table_name='master_data_crosswalk')
    op.drop_index(op.f('ix_master_data_crosswalk_target_id'), table_name='master_data_crosswalk')
    op.drop_index(op.f('ix_master_data_crosswalk_source_type'), table_name='master_data_crosswalk')
    op.drop_index(op.f('ix_master_data_crosswalk_source_id'), table_name='master_data_crosswalk')
    op.drop_index(op.f('ix_master_data_crosswalk_relation_type'), table_name='master_data_crosswalk')
    op.drop_index(op.f('ix_master_data_crosswalk_id'), table_name='master_data_crosswalk')
    op.drop_table('master_data_crosswalk')
