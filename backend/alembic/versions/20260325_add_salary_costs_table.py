"""Add salary_costs table for lønnskostnad import

Revision ID: 20260325_add_salary_costs
Revises: 20260323_merge_unitfields_srs, 89b2b309a9d9
Create Date: 2026-03-25

Uses raw SQL only. No named PG enum types (Column(String) throughout).
"""
from alembic import op
from sqlalchemy import text, inspect

revision = '20260325_add_salary_costs'
down_revision = ('20260323_merge_unitfields_srs', '89b2b309a9d9')
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    existing = inspector.get_table_names()

    if 'salary_costs' not in existing:
        op.execute(text("""
            CREATE TABLE salary_costs (
                salary_cost_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id         UUID REFERENCES properties(property_id),
                year                INTEGER NOT NULL,
                faste_stillinger    NUMERIC(19,4) NOT NULL DEFAULT 0,
                vikarer             NUMERIC(19,4) NOT NULL DEFAULT 0,
                arbeidsgiveravgift  NUMERIC(19,4) NOT NULL DEFAULT 0,
                institution_name_raw VARCHAR(500),
                import_batch_id     VARCHAR(100),
                imported_at         TIMESTAMPTZ DEFAULT now(),
                UNIQUE (property_id, year)
            )
        """))

        op.execute(text("CREATE INDEX IF NOT EXISTS ix_salary_costs_property ON salary_costs(property_id)"))
        op.execute(text("CREATE INDEX IF NOT EXISTS ix_salary_costs_year ON salary_costs(year)"))


def downgrade():
    op.execute(text("DROP INDEX IF EXISTS ix_salary_costs_year"))
    op.execute(text("DROP INDEX IF EXISTS ix_salary_costs_property"))
    op.execute(text("DROP TABLE IF EXISTS salary_costs CASCADE"))
