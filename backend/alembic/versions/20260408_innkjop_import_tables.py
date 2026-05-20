"""innkjop_import_tables

Legg til data_source + is_partial_year på salary_costs.
Opprett innkjop_nasjonal_summary for aggregerte innkjøpskategorier.

Revision ID: 20260408_innkjop_import
Revises: 20260328_salary_kategori
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "20260408_innkjop_import"
down_revision = "20260328_salary_kategori"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- salary_costs: legg til sporingsfelt ---
    op.add_column("salary_costs", sa.Column(
        "data_source", sa.String(100), nullable=True,
        comment="Kilde for dataen, f.eks. 'innkjopsanalyse_2026_excel' eller 'csv_import'"
    ))
    op.add_column("salary_costs", sa.Column(
        "is_partial_year", sa.Boolean(), nullable=False,
        server_default="false",
        comment="True dersom årstallet kun dekker en del av året (f.eks. 2026 i delårsekstrakt)"
    ))

    # --- Ny tabell: innkjop_nasjonal_summary ---
    op.create_table(
        "innkjop_nasjonal_summary",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True),
                  primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ar", sa.Integer(), nullable=False),
        sa.Column("kategori", sa.String(200), nullable=False,
                  comment="Hoved-innkjøpskategori, f.eks. 'Kjøp av barnevernstjenester'"),
        sa.Column("underkategori", sa.String(200), nullable=True,
                  comment="Underkategori, f.eks. 'Enkeltplasser private kommersielle'"),
        sa.Column("region", sa.String(100), nullable=True,
                  comment="Region, f.eks. 'Region Øst'. NULL = nasjonal sum"),
        sa.Column("belop", sa.Numeric(19, 4), nullable=False),
        sa.Column("kilde_fane", sa.String(100), nullable=True,
                  comment="Fanens navn i kildefilen"),
        sa.Column("import_batch_id", sa.String(100), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=True),
        sa.UniqueConstraint(
            "ar", "kategori", "underkategori", "region",
            name="uq_innkjop_ar_kat_underkat_region"
        ),
    )
    op.create_index("ix_innkjop_ar",        "innkjop_nasjonal_summary", ["ar"])
    op.create_index("ix_innkjop_kategori",   "innkjop_nasjonal_summary", ["kategori"])
    op.create_index("ix_innkjop_region",     "innkjop_nasjonal_summary", ["region"])


def downgrade() -> None:
    op.drop_index("ix_innkjop_region",   "innkjop_nasjonal_summary")
    op.drop_index("ix_innkjop_kategori", "innkjop_nasjonal_summary")
    op.drop_index("ix_innkjop_ar",       "innkjop_nasjonal_summary")
    op.drop_table("innkjop_nasjonal_summary")
    op.drop_column("salary_costs", "is_partial_year")
    op.drop_column("salary_costs", "data_source")
