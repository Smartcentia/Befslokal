"""SRS Regnskap Fase 1: koststed på Property, ny GLTransaction, KoststedMapping, FixedAsset

Revision ID: 20260320_srs_fase1
Revises: 20260312_dept_code_name
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260320_srs_fase1"
down_revision = "20260312_dept_code_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Property: nye SRS-felt
    # -----------------------------------------------------------------------
    op.add_column("properties", sa.Column("koststed_kode", sa.String(20), nullable=True))
    op.add_column("properties", sa.Column("leiekontrakt_utlop", sa.Date(), nullable=True))
    op.create_index("ix_properties_koststed_kode", "properties", ["koststed_kode"])

    # -----------------------------------------------------------------------
    # 2. gl_transactions: dropp gammel og bygg ny (data er allerede slettet)
    # -----------------------------------------------------------------------
    op.drop_table("gl_transactions")
    op.create_table(
        "gl_transactions",
        sa.Column("transaction_id", UUID(as_uuid=True), primary_key=True),
        # Sporing
        sa.Column("batch_id",        sa.String(100), nullable=True),
        sa.Column("imported_by",     sa.String(100), nullable=True),
        sa.Column("source_file_ref", sa.String(500), nullable=True),
        # Agresso-felt
        sa.Column("ba_kode",         sa.String(10),  nullable=True),
        sa.Column("bilagsnr",        sa.String(50),  nullable=True),
        sa.Column("bilagsdato",      sa.Date(),      nullable=True),
        sa.Column("periode",         sa.String(6),   nullable=True),   # YYYYMM
        sa.Column("ar",              sa.Integer(),   nullable=True),
        sa.Column("maaned",          sa.Integer(),   nullable=True),
        sa.Column("konto",           sa.String(20),  nullable=True),
        sa.Column("konto_navn",      sa.String(200), nullable=True),
        sa.Column("av_konto",        sa.String(20),  nullable=True),
        sa.Column("region",          sa.String(50),  nullable=True),
        sa.Column("dim1_kode",       sa.String(20),  nullable=True),
        sa.Column("dim1_navn",       sa.String(200), nullable=True),
        sa.Column("dim2_kode",       sa.String(20),  nullable=True),
        sa.Column("dim2_navn",       sa.String(200), nullable=True),
        sa.Column("dim3_kode",       sa.String(20),  nullable=True),
        sa.Column("dim4_kode",       sa.String(20),  nullable=True),
        sa.Column("dim5_kode",       sa.String(20),  nullable=True),
        sa.Column("dim6_anlegg_id",  sa.String(20),  nullable=True),
        sa.Column("dim6_ansatt_id",  sa.String(20),  nullable=True),
        sa.Column("dim7_kode",       sa.String(20),  nullable=True),
        sa.Column("tekst",           sa.String(500), nullable=True),
        sa.Column("belop",           sa.Numeric(19, 4), nullable=False),
        sa.Column("leverandor_id",   sa.String(20),  nullable=True),
        sa.Column("leverandor_navn", sa.String(200), nullable=True),
        # Berikede felt
        sa.Column("property_id",     UUID(as_uuid=True),
                  sa.ForeignKey("properties.property_id"), nullable=True),
        sa.Column("srs_kategori",    sa.String(20),  nullable=True),
        sa.Column("is_statsbygg",    sa.Boolean(),   nullable=False, server_default="false"),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gl_bilagsnr",  "gl_transactions", ["bilagsnr"])
    op.create_index("ix_gl_konto",     "gl_transactions", ["konto"])
    op.create_index("ix_gl_dim1_kode", "gl_transactions", ["dim1_kode"])
    op.create_index("ix_gl_periode",   "gl_transactions", ["periode"])
    op.create_index("ix_gl_ar",        "gl_transactions", ["ar"])
    op.create_index("ix_gl_property",  "gl_transactions", ["property_id"])

    # -----------------------------------------------------------------------
    # 3. budget: dropp gammel (tom) og gjenoppbygg med Numeric
    # -----------------------------------------------------------------------
    op.drop_table("budget")
    op.create_table(
        "budget",
        sa.Column("budget_id",   UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", UUID(as_uuid=True),
                  sa.ForeignKey("properties.property_id"), nullable=False),
        sa.Column("year",        sa.Integer(),      nullable=False),
        sa.Column("month",       sa.Integer(),      nullable=False),
        sa.Column("category",    sa.String(100),    nullable=False),
        sa.Column("amount",      sa.Numeric(19, 4), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(),     nullable=False, server_default="false"),
        sa.Column("data_source", sa.String(100),    nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at",  sa.DateTime(timezone=True), nullable=True),
    )

    # -----------------------------------------------------------------------
    # 4. koststed_mapping (ny)
    # -----------------------------------------------------------------------
    op.create_table(
        "koststed_mapping",
        sa.Column("koststed_kode",    sa.String(20),  primary_key=True),
        sa.Column("koststed_navn",    sa.String(200), nullable=True),
        sa.Column("region",           sa.String(50),  nullable=True),
        sa.Column("eksempel_adresse", sa.String(500), nullable=True),
        sa.Column("property_id",      UUID(as_uuid=True),
                  sa.ForeignKey("properties.property_id"), nullable=True),
    )

    # -----------------------------------------------------------------------
    # 5. fixed_assets (ny)
    # -----------------------------------------------------------------------
    op.create_table(
        "fixed_assets",
        sa.Column("id",              UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_name",      sa.String(500), nullable=False),
        sa.Column("property_id",     UUID(as_uuid=True),
                  sa.ForeignKey("properties.property_id"), nullable=True),
        sa.Column("koststed_kode",   sa.String(20),  nullable=False),
        sa.Column("agresso_dim6_id", sa.String(20),  nullable=True),
        # Inngangsverdier
        sa.Column("original_account",  sa.String(20),     nullable=True),
        sa.Column("purchase_date",     sa.Date(),         nullable=True),
        sa.Column("acquisition_cost",  sa.Numeric(19, 4), nullable=False),
        # SRS-beregning
        sa.Column("opening_balance_value",       sa.Numeric(19, 4), nullable=True),
        sa.Column("monthly_depreciation_amount", sa.Numeric(19, 4), nullable=True),
        sa.Column("remaining_months_at_start",   sa.Integer(),      nullable=True),
        sa.Column("lease_end_date",              sa.Date(),         nullable=True),
        # Regnskapsstyring
        sa.Column("depreciation_account",   sa.String(20), nullable=True, server_default="'6010'"),
        sa.Column("accum_depr_account",     sa.String(20), nullable=True, server_default="'1269'"),
        sa.Column("neutralization_account", sa.String(20), nullable=True, server_default="'3390'"),
        sa.Column("financing_account",      sa.String(20), nullable=True, server_default="'3390'"),
        # Status
        sa.Column("is_grouped",           sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_fully_depreciated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("srs_status",           sa.String(20), nullable=False, server_default="'Aktiv'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_asset_property",  "fixed_assets", ["property_id"])
    op.create_index("ix_asset_koststed",  "fixed_assets", ["koststed_kode"])
    op.create_index("ix_asset_dim6",      "fixed_assets", ["agresso_dim6_id"])


def downgrade() -> None:
    op.drop_table("fixed_assets")
    op.drop_table("koststed_mapping")
    op.drop_table("budget")
    op.drop_table("gl_transactions")
    op.drop_column("properties", "leiekontrakt_utlop")
    op.drop_index("ix_properties_koststed_kode", table_name="properties")
    op.drop_column("properties", "koststed_kode")
