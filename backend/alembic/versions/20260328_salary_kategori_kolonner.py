"""salary_kategori_kolonner

Revision ID: 20260328_salary_kategori
Revises: 20260327_gl_kategori_kolonner
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "20260328_salary_kategori"
down_revision = ("20260325_add_salary_costs", "20260327_gl_kategori")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("salary_costs", sa.Column("turnustillegg",     sa.Numeric(19, 4), nullable=True))
    op.add_column("salary_costs", sa.Column("pensjonspremie",    sa.Numeric(19, 4), nullable=True))
    op.add_column("salary_costs", sa.Column("midlertidige",      sa.Numeric(19, 4), nullable=True))
    op.add_column("salary_costs", sa.Column("turnustillegg_vik", sa.Numeric(19, 4), nullable=True))
    op.add_column("salary_costs", sa.Column("overtid_faste",     sa.Numeric(19, 4), nullable=True))
    op.add_column("salary_costs", sa.Column("overtid_midl",      sa.Numeric(19, 4), nullable=True))
    op.add_column("salary_costs", sa.Column("aga_spk",           sa.Numeric(19, 4), nullable=True))


def downgrade() -> None:
    for col in ["aga_spk", "overtid_midl", "overtid_faste", "turnustillegg_vik",
                "midlertidige", "pensjonspremie", "turnustillegg"]:
        op.drop_column("salary_costs", col)
