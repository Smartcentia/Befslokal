"""create behovsmeldinger table

Revision ID: 20260510c_create_behovsmeldinger
Revises: 20260510b_create_system_settings
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260510c_create_behovsmeldinger'
down_revision = '20260510b_create_system_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'behovsmeldinger',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tittel', sa.String(255), nullable=False),
        sa.Column('beskrivelse', sa.Text(), nullable=True),
        sa.Column('kategori', sa.String(50), nullable=True),
        sa.Column('prioritet', sa.String(20), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='Ny'),
        sa.Column('opprettet_av', sa.String(255), nullable=False),
        sa.Column('eiendom_navn', sa.String(255), nullable=True),
        sa.Column('admin_kommentar', sa.Text(), nullable=True),
        sa.Column('er_arkivert', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('opprettet_dato', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('oppdatert_dato', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_behovsmeldinger_opprettet_av', 'behovsmeldinger', ['opprettet_av'])
    op.create_index('ix_behovsmeldinger_status', 'behovsmeldinger', ['status'])


def downgrade() -> None:
    op.drop_index('ix_behovsmeldinger_status', 'behovsmeldinger')
    op.drop_index('ix_behovsmeldinger_opprettet_av', 'behovsmeldinger')
    op.drop_table('behovsmeldinger')
