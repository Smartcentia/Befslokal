"""Fase 4 Bygningsstruktur: buildings, floors, spaces + unit FK-kolonner

Revision ID: 20260421_building_structure
Revises: 20260421_maintenance_plan  (worktree head – set to actual head when merged)
Create Date: 2026-04-21

Bruker raw SQL / op.create_table. Ingen named PG enum types (Column(String) gjennomgående).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, inspect

revision = '20260421_building_structure'
down_revision = '20260421_maintenance_plan'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # ------------------------------------------------------------------
    # 1. buildings
    # ------------------------------------------------------------------
    if 'buildings' not in existing_tables:
        op.create_table(
            'buildings',
            sa.Column('building_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('property_id', UUID(as_uuid=True),
                      sa.ForeignKey('properties.property_id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('building_code', sa.String(20), nullable=True),
            sa.Column('year_built', sa.Integer(), nullable=True),
            sa.Column('building_type', sa.String(50), nullable=True, server_default='main'),
            sa.Column('floors_above_ground', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('floors_below_ground', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('total_area_sqm', sa.Float(), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.text('now()')),
        )
        op.create_index('ix_buildings_property_id', 'buildings', ['property_id'])

    # ------------------------------------------------------------------
    # 2. floors
    # ------------------------------------------------------------------
    if 'floors' not in existing_tables:
        op.create_table(
            'floors',
            sa.Column('floor_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('building_id', UUID(as_uuid=True),
                      sa.ForeignKey('buildings.building_id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('floor_number', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('area_sqm', sa.Float(), nullable=True),
        )
        op.create_index('ix_floors_building_id', 'floors', ['building_id'])

    # ------------------------------------------------------------------
    # 3. spaces
    # ------------------------------------------------------------------
    if 'spaces' not in existing_tables:
        op.create_table(
            'spaces',
            sa.Column('space_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('floor_id', UUID(as_uuid=True),
                      sa.ForeignKey('floors.floor_id', ondelete='SET NULL'),
                      nullable=True),
            sa.Column('property_id', UUID(as_uuid=True),
                      sa.ForeignKey('properties.property_id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('unit_id', UUID(as_uuid=True),
                      sa.ForeignKey('units.unit_id', ondelete='SET NULL'),
                      nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('space_type', sa.String(50), nullable=True, server_default='room'),
            sa.Column('area_sqm', sa.Float(), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
        )
        op.create_index('ix_spaces_floor_id', 'spaces', ['floor_id'])
        op.create_index('ix_spaces_property_id', 'spaces', ['property_id'])

    # ------------------------------------------------------------------
    # 4. units: legg til building_id og floor_id (nullable)
    # ------------------------------------------------------------------
    existing_unit_cols = {c['name'] for c in inspector.get_columns('units')}

    if 'building_id' not in existing_unit_cols:
        op.add_column(
            'units',
            sa.Column('building_id', UUID(as_uuid=True),
                      sa.ForeignKey('buildings.building_id', ondelete='SET NULL'),
                      nullable=True)
        )
        op.create_index('ix_units_building_id', 'units', ['building_id'])

    if 'floor_id' not in existing_unit_cols:
        op.add_column(
            'units',
            sa.Column('floor_id', UUID(as_uuid=True),
                      sa.ForeignKey('floors.floor_id', ondelete='SET NULL'),
                      nullable=True)
        )
        op.create_index('ix_units_floor_id', 'units', ['floor_id'])


def downgrade():
    # Fjern indekser og kolonner på units
    op.drop_index('ix_units_floor_id', table_name='units', if_exists=True)
    op.drop_index('ix_units_building_id', table_name='units', if_exists=True)
    op.drop_column('units', 'floor_id')
    op.drop_column('units', 'building_id')

    # Fjern tabeller
    op.drop_table('spaces')
    op.drop_table('floors')
    op.drop_table('buildings')
