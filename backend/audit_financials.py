#!/usr/bin/env python3
"""Comprehensive financial data audit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
import json

def get_database_url():
    """Get database URL, convert to psycopg2 if needed."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url

def main():
    engine = create_engine(get_database_url())
    
    print("=" * 90)
    print("COMPREHENSIVE FINANCIAL DATA AUDIT")
    print("=" * 90)
    
    with engine.connect() as conn:
        # 1. DASHBOARD METRICS
        print("\n📊 DASHBOARD METRICS")
        print("-" * 90)
        result = conn.execute(text("SELECT * FROM dashboard_metrics LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"  Total Properties: {row[1]:,}")
            print(f"  Total Contracts: {row[2]:,}")
            print(f"  Total Annual Rent: {row[4]:,.2f} NOK")
            print(f"  Total Maintenance Cost: {row[5]:,.2f} NOK" if row[5] else "  Total Maintenance Cost: NULL")
            print(f"  Last Updated: {row[6]}")
        
        # 2. CONTRACTS WITH FINANCIAL DATA
        print("\n💰 CONTRACT FINANCIAL DATA")
        print("-" * 90)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN amount->>'annual_rent' IS NOT NULL THEN 1 END) as with_rent,
                SUM((amount->>'annual_rent')::float) as total_annual_rent,
                AVG((amount->>'annual_rent')::float) as avg_annual_rent,
                MIN((amount->>'annual_rent')::float) as min_rent,
                MAX((amount->>'annual_rent')::float) as max_rent
            FROM contracts
            WHERE amount->>'annual_rent' IS NOT NULL
        """))
        row = result.fetchone()
        print(f"  Total Contracts: {row[0]:,}")
        print(f"  Contracts with Rent Data: {row[1]:,}")
        if row[2]:
            print(f"  Total Annual Rent: {row[2]:,.2f} NOK")
            print(f"  Average Annual Rent: {row[3]:,.2f} NOK")
            print(f"  Min Annual Rent: {row[4]:,.2f} NOK")
            print(f"  Max Annual Rent: {row[5]:,.2f} NOK")
        
        # 3. PROPERTIES WITH EXTERNAL DATA (FINANCIALS)
        print("\n🏢 PROPERTY FINANCIAL DATA (external_data)")
        print("-" * 90)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN external_data IS NOT NULL THEN 1 END) as with_external_data,
                COUNT(CASE WHEN external_data::text LIKE '%financials%' THEN 1 END) as with_financials,
                COUNT(CASE WHEN external_data::text LIKE '%manual_expenses%' THEN 1 END) as with_manual_expenses
            FROM properties
        """))
        row = result.fetchone()
        print(f"  Total Properties: {row[0]:,}")
        print(f"  With external_data: {row[1]:,} ({row[1]*100//row[0] if row[0] else 0}%)")
        print(f"  With 'financials' data: {row[2]:,} ({row[2]*100//row[0] if row[0] else 0}%)")
        print(f"  With 'manual_expenses': {row[3]:,} ({row[3]*100//row[0] if row[0] else 0}%)")
        
        # 4. SAMPLE FINANCIAL DATA FROM PROPERTIES
        print("\n💼 SAMPLE PROPERTY FINANCIALS (First 3)")
        print("-" * 90)
        result = conn.execute(text("""
            SELECT 
                property_id,
                address,
                city,
                external_data
            FROM properties
            WHERE external_data::text LIKE '%financials%'
            LIMIT 3
        """))
        for i, row in enumerate(result, 1):
            print(f"\n  Property {i}: {row[1]}, {row[2]}")
            if row[3]:
                ext_data = row[3]
                if 'financials' in ext_data:
                    fins = ext_data.get('financials', {})
                    if 'manual_expenses' in fins:
                        expenses = fins['manual_expenses']
                        print(f"    Manual Expenses: {len(expenses)} items")
                        total = sum(item.get('amount', 0) for item in expenses)
                        print(f"    Total: {total:,.2f} NOK")
                    if 'total_spend_csv' in fins:
                        print(f"    CSV Total Spend: {fins['total_spend_csv']:,.2f} NOK")
        
        # 5. UNITS DATA
        print("\n🏗️  UNIT DATA")
        print("-" * 90)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN area_sqm IS NOT NULL THEN 1 END) as with_area,
                SUM(area_sqm) as total_area,
                AVG(area_sqm) as avg_area,
                COUNT(DISTINCT purpose) as distinct_purposes
            FROM units
        """))
        row = result.fetchone()
        print(f"  Total Units: {row[0]:,}")
        print(f"  With Area Data: {row[1]:,} ({row[1]*100//row[0] if row[0] else 0}%)")
        print(f"  Total Area: {row[2]:,.2f} sqm" if row[2] else "  Total Area: NULL")
        print(f"  Average Area: {row[3]:,.2f} sqm" if row[3] else "  Average Area: NULL")
        print(f"  Distinct Purposes: {row[4]}")
        
        # 6. PARTIES DATA
        print("\n👥 PARTY DATA")
        print("-" * 90)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN orgnr IS NOT NULL AND orgnr != '000000000' THEN 1 END) as with_orgnr,
                COUNT(CASE WHEN contact_email IS NOT NULL THEN 1 END) as with_email,
                COUNT(CASE WHEN external_data IS NOT NULL THEN 1 END) as with_external_data
            FROM parties
        """))
        row = result.fetchone()
        print(f"  Total Parties: {row[0]:,}")
        print(f"  With Valid OrgNr: {row[1]:,} ({row[1]*100//row[0] if row[0] else 0}%)")
        print(f"  With Contact Email: {row[2]:,} ({row[2]*100//row[0] if row[0] else 0}%)")
        print(f"  With External Data: {row[3]:,} ({row[3]*100//row[0] if row[0] else 0}%)")
        
        # 7. MISSING DATA SUMMARY
        print("\n⚠️  MISSING DATA SUMMARY")
        print("-" * 90)
        
        # Missing coordinates
        result = conn.execute(text("SELECT COUNT(*) FROM properties WHERE latitude IS NULL OR longitude IS NULL"))
        missing_coords = result.scalar()
        print(f"  Properties missing coordinates: {missing_coords:,}")
        
        # Missing contract rent
        result = conn.execute(text("SELECT COUNT(*) FROM contracts WHERE amount->>'annual_rent' IS NULL"))
        missing_rent = result.scalar()
        print(f"  Contracts missing rent data: {missing_rent:,}")
        
        # Missing property financials
        result = conn.execute(text("SELECT COUNT(*) FROM properties WHERE external_data IS NULL OR external_data::text NOT LIKE '%financials%'"))
        missing_financials = result.scalar()
        print(f"  Properties missing financial data: {missing_financials:,}")
        
        # Missing unit area
        result = conn.execute(text("SELECT COUNT(*) FROM units WHERE area_sqm IS NULL"))
        missing_area = result.scalar()
        print(f"  Units missing area data: {missing_area:,}")
        
        # Missing party org numbers
        result = conn.execute(text("SELECT COUNT(*) FROM parties WHERE orgnr IS NULL OR orgnr = '000000000'"))
        missing_orgnr = result.scalar()
        print(f"  Parties missing org numbers: {missing_orgnr:,}")
        
        print("\n" + "=" * 90)
        print("✅ Financial Audit Complete")
        print("=" * 90)

if __name__ == "__main__":
    main()
