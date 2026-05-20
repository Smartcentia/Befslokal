"""Add property_annual_costs table

Revision ID: 20260226_property_costs
Revises: 20260225_unit_address
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260226_property_costs"
down_revision = "20260225_unit_address"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create the property_annual_costs table
    op.create_table(
        "property_annual_costs",
        sa.Column("property_annual_cost_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contracts.contract_id", ondelete="SET NULL"), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        
        sa.Column("kpi_adjusted_rent", sa.Float(), nullable=True),
        sa.Column("internal_maintenance", sa.Float(), nullable=True),
        sa.Column("common_costs", sa.Float(), nullable=True),
        sa.Column("energy_costs", sa.Float(), nullable=True),
        sa.Column("heating_costs", sa.Float(), nullable=True),
        sa.Column("cleaning_costs", sa.Float(), nullable=True),
        sa.Column("parking_rent", sa.Float(), nullable=True),
        sa.Column("caretaker_cost", sa.Float(), nullable=True),
        sa.Column("card_reader_cost", sa.Float(), nullable=True),
        
        sa.Column("other_costs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("external_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for the foreign keys and lookup fields
    op.create_index("ix_property_annual_costs_property_id", "property_annual_costs", ["property_id"], unique=False)
    op.create_index("ix_property_annual_costs_contract_id", "property_annual_costs", ["contract_id"], unique=False)
    op.create_index("ix_property_annual_costs_year", "property_annual_costs", ["year"], unique=False)

def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_property_annual_costs_year", table_name="property_annual_costs")
    op.drop_index("ix_property_annual_costs_contract_id", table_name="property_annual_costs")
    op.drop_index("ix_property_annual_costs_property_id", table_name="property_annual_costs")
    
    # Drop the table
    op.drop_table("property_annual_costs")
