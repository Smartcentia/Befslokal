import asyncio
import os
import sys
from sqlalchemy import select, func, text

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from backend.app.db.session import SessionLocal, engine
from backend.app.domains.core.models.property import Property
from backend.app.domains.core.models.contract import Contract
from backend.app.domains.core.models.unit import Unit
from backend.app.models.external_api_data import ExternalApiData

# Import other models for mapper initialization
from backend.app.domains.core.models.party import Party
from backend.app.domains.hms.models.risk import RiskAssessment
from backend.app.domains.hms.models.internal_control import InternalControlCase
from backend.app.domains.core.models.user import User

async def audit():
    async with SessionLocal() as session:
        print("\n--- 1. DATABASE SCHEMA AUDIT ---")
        async with engine.connect() as conn:
            for table in ['properties', 'contracts', 'units', 'external_api_data']:
                res = await conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
                print(f"\nTable: {table}")
                for row in res.fetchall():
                    print(f"  - {row[0]}: {row[1]}")

        print("\n--- 2. DATA CONSISTENCY AUDIT ---")
        # Total counts
        prop_count = await session.execute(select(func.count()).select_from(Property))
        unit_count = await session.execute(select(func.count()).select_from(Unit))
        contract_count = await session.execute(select(func.count()).select_from(Contract))
        print(f"Total Properties: {prop_count.scalar()}")
        print(f"Total Units:      {unit_count.scalar()}")
        print(f"Total Contracts:  {contract_count.scalar()}")

        # Orphaned Units
        orphaned_units = await session.execute(select(func.count()).select_from(Unit).where(Unit.property_id == None))
        print(f"Orphaned Units (no property): {orphaned_units.scalar()}")

        # Orphaned Contracts
        orphaned_contracts = await session.execute(select(func.count()).select_from(Contract).where(Contract.unit_id == None))
        print(f"Orphaned Contracts (no unit): {orphaned_contracts.scalar()}")

        # Missing Geographical Data
        missing_geo = await session.execute(select(func.count()).select_from(Property).where(Property.city == None))
        print(f"Properties missing City: {missing_geo.scalar()}")

        print("\n--- 3. EXTERNAL API CACHE AUDIT ---")
        cache_count = await session.execute(select(func.count()).select_from(ExternalApiData))
        print(f"Total Cached API Responses: {cache_count.scalar()}")
        
        recent_cache = await session.execute(select(ExternalApiData).order_by(ExternalApiData.fetched_at.desc()).limit(5))
        print("\nRecent Cache Entries:")
        for c in recent_cache.scalars():
            print(f"  - Entity: {c.entity_id} | Type: {c.entity_type} | Saved At: {c.fetched_at}")

        print("\n--- 4. FINANCIAL DATA AUDIT ---")
        # Check if properties have financial data in JSONB
        has_financials = await session.execute(
            text("SELECT count(*) FROM properties WHERE external_data->'financials' IS NOT NULL")
        )
        print(f"Properties with 'financials' JSONB: {has_financials.scalar()}")

        # Check for non-zero maintenance costs in a sample
        sample_costs = await session.execute(
            text("SELECT name, (external_data->'financials'->>'municipal_fees')::float as fee "
                 "FROM properties WHERE external_data->'financials'->>'municipal_fees' IS NOT NULL LIMIT 2")
        )
        print("\nFinancial Samples (Municipal Fees):")
        for row in sample_costs.fetchall():
            print(f"  - {row[0]}: {row[1]}")

        print("\n--- 5. DATA QUALITY SAMPLES ---")
        samples = await session.execute(select(Property).where(Property.region != None).limit(3))
        for p in samples.scalars():
            print(f"Property: {p.name}")
            print(f"  Address: {p.address}, {p.postal_code} {p.city}")
            print(f"  Region:  {p.region}")

if __name__ == "__main__":
    asyncio.run(audit())
