import os
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:Sunnyowl_6533@db.vwvhxcqxadblrftuvsds.supabase.co:5432/postgres"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS property_annual_costs (
    property_annual_cost_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
    contract_id UUID REFERENCES contracts(contract_id) ON DELETE SET NULL,
    year INTEGER NOT NULL,
    
    kpi_adjusted_rent DOUBLE PRECISION,
    internal_maintenance DOUBLE PRECISION,
    common_costs DOUBLE PRECISION,
    energy_costs DOUBLE PRECISION,
    heating_costs DOUBLE PRECISION,
    cleaning_costs DOUBLE PRECISION,
    parking_rent DOUBLE PRECISION,
    caretaker_cost DOUBLE PRECISION,
    card_reader_cost DOUBLE PRECISION,
    
    other_costs JSONB,
    external_data JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_property_annual_costs_property_id ON property_annual_costs (property_id);
CREATE INDEX IF NOT EXISTS ix_property_annual_costs_contract_id ON property_annual_costs (contract_id);
CREATE INDEX IF NOT EXISTS ix_property_annual_costs_year ON property_annual_costs (year);

INSERT INTO alembic_version (version_num) VALUES ('20260226_annual_costs') ON CONFLICT DO NOTHING;
"""

async def run():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("Executing table creation...")
    await conn.execute(CREATE_TABLE_SQL)
    print("Done!")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
