#!/usr/bin/env python3
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
# Import all models
import app.db.base
from app.services.financial_analysis_service import FinancialAnalysisService
from app.services.data_health_service import data_health_service
from app.services.api_clients.kartverket_client import KartverketClient

# Setup DB
RAW_DB_URL = os.getenv("DATABASE_URL")

# Fix URL for asyncpg
# 1. Ensure driver
if "postgresql://" in RAW_DB_URL and "asyncpg" not in RAW_DB_URL:
    RAW_DB_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# 2. Fix sslmode -> ssl (asyncpg expects 'ssl', psycopg2 expects 'sslmode')
if "sslmode=require" in RAW_DB_URL:
    RAW_DB_URL = RAW_DB_URL.replace("sslmode=require", "ssl=require")
elif "sslmode" in RAW_DB_URL:
    # Handle bare ?sslmode
    RAW_DB_URL = RAW_DB_URL.replace("?sslmode", "?ssl=require")
    RAW_DB_URL = RAW_DB_URL.replace("&sslmode", "&ssl=require")

# 3. Ensure ssl if missing (Generic check for cloud DBs usually requiring SSL)
if "sslmode" not in RAW_DB_URL and "ssl=" not in RAW_DB_URL and "localhost" not in RAW_DB_URL:
    if "?" in RAW_DB_URL:
        RAW_DB_URL += "&ssl=require"
    else:
        RAW_DB_URL += "?ssl=require"

print(f"Connecting to: {RAW_DB_URL.split('@')[-1]}") # Log safe part

engine = create_async_engine(RAW_DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_financial():
    print("🔹 Testing Financial Analysis Service...")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Patterns
            print("   Fetching patterns...", end=" ")
            patterns = await FinancialAnalysisService.get_common_patterns(db)
            print(f"✅ OK ({len(patterns.get('common_patterns', []))} patterns found)")
            
            # 2. Search
            # Inspect first property to find a valid search term
            stmt = select(app.db.base.Property).limit(1)
            res = await db.execute(stmt)
            p = res.scalar_one_or_none()
            name = p.name if p else "Unknown"
            print(f"   Testing search '{name[:5]}'...", end=" ")
            if p:
                results = await FinancialAnalysisService.search_properties(db, name[:3])
                print(f"✅ OK ({len(results)} results found)")
                if results:
                    r = results[0]
                    print(f"      Summary: Rent={r['rent']}, Costs={r['costs']}")
                    
                    # Verify details
                    if r['costs'] > 0:
                        print(f"      ✅ Costs found! ({r['costs']} NOK)")
                    else:
                        print(f"      ⚠️ No costs found for {r['name']} (might be expected if random variance hit 0 or no area)")
                        
                    # Detailed check
                    prop_id = r.get('property_id') or r.get('id')
                    print(f"      Fetching details for {prop_id}...", end=" ")
                    details = await FinancialAnalysisService.get_property_analysis(db, prop_id)
                    
            
            # Verify Data Source (Real vs Synthetic)
            stmt_src = select(app.db.base.Property).where(app.db.base.Property.property_id == prop_id)
            res_src = await db.execute(stmt_src)
            prop_src = res_src.scalar_one_or_none()
            
            # Debug print
            print(f"      🕵️ External Data Keys: {list(prop_src.external_data.keys()) if prop_src and prop_src.external_data else 'None'}")
            
            source_type = prop_src.external_data.get('data_source', 'test_unknown') if prop_src and prop_src.external_data else 'unknown_no_ext'
            
            if details and details.get('num_expenses', 0) > 0:
                print(f"✅ OK")
                print(f"      📊 Data Source: {source_type.upper()}")
                print(f"      💰 Financials: {len(details.get('cost_by_category', []))} categories")
            else:
                print("⚠️ No details found")
                
            # Scan for any REAL_LEDGER
            print("\n   Scanning for Real Ledger Data...", end=" ")
            stmt_all = select(app.db.base.Property)
            res_all = await db.execute(stmt_all)
            all_props = res_all.scalars().all()
            
            real_count = sum(1 for p in all_props if p.external_data and p.external_data.get('data_source') == 'real_ledger')
            syn_count = sum(1 for p in all_props if p.external_data and p.external_data.get('data_source') == 'synthetic')
            
            print(f"✅ Found {real_count} Real / {syn_count} Synthetic properties.")
            if real_count > 0:
                # Print name of one real property
                real_prop = next(p for p in all_props if p.external_data and p.external_data.get('data_source') == 'real_ledger')
                print(f"      Example Real Property: {real_prop.name}")

        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

async def test_health():
    print("\n🔹 Testing Data Health Service...")
    async with AsyncSessionLocal() as db:
        try:
            print("   Checking integrity...", end=" ")
            integrity = await data_health_service.check_integrity(db)
            print(f"✅ OK (Issues found: {len(integrity.get('issues', []))})")
            
            print("   Getting stats...", end=" ")
            stats = await data_health_service.get_data_stats(db)
            print(f"✅ OK (Properties: {stats.get('properties_count')})")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")

async def test_kartverket():
    print("\n🔹 Testing Kartverket Integration (Risk/Geocoding)...")
    client = KartverketClient()
    try:
        print("   Searching 'Storgata 1, Oslo'...", end=" ")
        res = await client.search_address("Storgata 1, Oslo")
        if res and res.get('latitude'):
            print(f"✅ OK (Lat: {res['latitude']})")
        else:
            print("⚠️ No coordinates returned (API might be reachable but no match)")
    except Exception as e:
        print(f"❌ FAILED: {e}")

async def main():
    print("="*60)
    print("ADMIN FEATURE VERIFICATION")
    print("="*60)
    
    try:
        await test_financial()
        await test_health()
        await test_kartverket()
    except Exception as e:
        print(f"Fatal test error: {e}")
    finally:
        await engine.dispose()
    
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())
