"""Fase 6 Organisasjonslag: organisations table + FK på users og properties

Revision ID: 20260421_organisations
Revises: 20260421_building_structure
Create Date: 2026-04-21

Ingen named PG enum types (Column(String) gjennomgående).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, inspect

revision = '20260421_organisations'
down_revision = '20260421_fdv_doc_embeddings'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # ------------------------------------------------------------------
    # 1. Opprett organisations-tabell
    # ------------------------------------------------------------------
    if 'organisations' not in existing_tables:
        op.create_table(
            'organisations',
            sa.Column('org_id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('region_code', sa.String(50), nullable=True, unique=True),
            sa.Column('org_nr', sa.String(9), nullable=True),
            sa.Column('contact_email', sa.String(200), nullable=True),
            sa.Column('budget_target_nok', sa.Numeric(19, 4), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        )

    # ------------------------------------------------------------------
    # 2. Seed 6 standard Bufetat-regioner
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO organisations (org_id, name, region_code, is_active, created_at)
        VALUES
          (gen_random_uuid(), 'Bufetat region Øst',   'Øst',    true, now()),
          (gen_random_uuid(), 'Bufetat region Vest',  'Vest',   true, now()),
          (gen_random_uuid(), 'Bufetat region Nord',  'Nord',   true, now()),
          (gen_random_uuid(), 'Bufetat region Sør',   'Sør',    true, now()),
          (gen_random_uuid(), 'Bufetat region Midt',  'Midt',   true, now()),
          (gen_random_uuid(), 'Bufdir',               'Bufdir', true, now())
        ON CONFLICT DO NOTHING
    """)

    # ------------------------------------------------------------------
    # 3. Legg til org_id FK på users
    # ------------------------------------------------------------------
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'org_id' not in users_columns:
        op.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organisations(org_id)"
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_users_org_id ON users (org_id)")

    # ------------------------------------------------------------------
    # 4. Legg til org_id FK på properties
    # ------------------------------------------------------------------
    properties_columns = [col['name'] for col in inspector.get_columns('properties')]
    if 'org_id' not in properties_columns:
        op.execute(
            "ALTER TABLE properties ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organisations(org_id)"
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_properties_org_id ON properties (org_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_properties_org_id")
    op.execute("DROP INDEX IF EXISTS ix_users_org_id")

    conn = op.get_bind()
    inspector = inspect(conn)

    properties_columns = [col['name'] for col in inspector.get_columns('properties')]
    if 'org_id' in properties_columns:
        op.drop_column('properties', 'org_id')

    users_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'org_id' in users_columns:
        op.drop_column('users', 'org_id')

    op.drop_table('organisations')
