"""phase 2 center model

Revision ID: phase_2_center_model
Revises: 20260115_183000_phase_1_schema
Create Date: 2026-01-16 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase_2_center_model'
down_revision = '9f8a7b6c5d4e'  # This is the actual revision ID from phase_1_schema.py
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # 1. Create centers table
    if 'centers' not in existing_tables:
        op.create_table('centers',
            sa.Column('center_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('region', sa.String(), nullable=True),
            sa.Column('emergency_contacts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('center_id')
        )

    # 2. Add columns to properties table if they don't exist
    existing_columns = [col['name'] for col in inspector.get_columns('properties')]
    
    if 'center_id' not in existing_columns:
        op.add_column('properties', sa.Column('center_id', sa.String(), nullable=True))
    
    if 'crisis_contacts' not in existing_columns:
        op.add_column('properties', sa.Column('crisis_contacts', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # 3. Add FK bare hvis constraint ikke finnes (unngår try/except som etterlater transaksjon aborted)
    if 'centers' in inspector.get_table_names():
        r = conn.execute(text("SELECT 1 FROM pg_constraint WHERE conname = 'fk_properties_center_id' LIMIT 1"))
        if r.scalar() is None:
            op.create_foreign_key('fk_properties_center_id', 'properties', 'centers', ['center_id'], ['center_id'])


def downgrade():
    conn = op.get_bind()
    # Sjekk og fjern kun hvis de finnes – unngår try/except som etterlater transaksjon aborted
    r = conn.execute(text("SELECT 1 FROM pg_constraint WHERE conname = 'fk_properties_center_id' LIMIT 1"))
    if r.scalar() is not None:
        op.drop_constraint('fk_properties_center_id', 'properties', type_='foreignkey')
    inspector = inspect(conn)
    if 'properties' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('properties')]
        if 'crisis_contacts' in cols:
            op.drop_column('properties', 'crisis_contacts')
        if 'center_id' in cols:
            op.drop_column('properties', 'center_id')
    if 'centers' in inspector.get_table_names():
        op.drop_table('centers')
