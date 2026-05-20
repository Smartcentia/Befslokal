"""add lokasjoner table and link properties

Revision ID: 20260423_lokasjoner
Revises: merge_cbb_af84
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260423_lokasjoner"
down_revision = "20260421_organisations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create lokasjoner table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS lokasjoner (
            lokasjon_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            navn            VARCHAR NOT NULL,
            adresse         VARCHAR,
            lokalisering_id VARCHAR,
            region          VARCHAR,
            merknad         VARCHAR,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_lokasjoner_lokalisering_id ON lokasjoner(lokalisering_id)"
    ))

    # 2. Add lokasjon_id FK column to properties
    op.execute(sa.text(
        "ALTER TABLE properties ADD COLUMN IF NOT EXISTS lokasjon_id UUID REFERENCES lokasjoner(lokasjon_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_properties_lokasjon_id ON properties(lokasjon_id)"
    ))

    # 3. Auto-populate lokasjoner from existing area + lokalisering_id groups.
    #    One lokasjon per unique (area, lokalisering_id) combination that has data.
    op.execute(sa.text("""
        INSERT INTO lokasjoner (lokasjon_id, navn, lokalisering_id, region)
        SELECT
            gen_random_uuid(),
            COALESCE(NULLIF(area, ''), lokalisering_id, 'Ukjent'),
            lokalisering_id,
            region
        FROM (
            SELECT DISTINCT
                area,
                lokalisering_id,
                region
            FROM properties
            WHERE area IS NOT NULL OR lokalisering_id IS NOT NULL
        ) AS grp
        ON CONFLICT DO NOTHING
    """))

    # 4. Link properties to their newly created lokasjon
    op.execute(sa.text("""
        UPDATE properties p
        SET lokasjon_id = l.lokasjon_id
        FROM lokasjoner l
        WHERE
            l.lokalisering_id IS NOT NULL
            AND p.lokalisering_id = l.lokalisering_id
            AND p.lokasjon_id IS NULL
    """))
    # For properties matched on area (where lokalisering_id is null)
    op.execute(sa.text("""
        UPDATE properties p
        SET lokasjon_id = l.lokasjon_id
        FROM lokasjoner l
        WHERE
            p.lokasjon_id IS NULL
            AND p.area IS NOT NULL
            AND l.lokalisering_id IS NULL
            AND l.navn = p.area
    """))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE properties DROP COLUMN IF EXISTS lokasjon_id"))
    op.execute(sa.text("DROP TABLE IF EXISTS lokasjoner"))
