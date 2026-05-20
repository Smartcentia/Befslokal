#!/usr/bin/env python3
"""Comprehensive contract data audit"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text
import pandas as pd

async def comprehensive_audit():
    async with SessionLocal() as db:
        print("=" * 70)
        print("📊 COMPREHENSIVE CONTRACT DATA AUDIT")
        print("=" * 70)
        
        # 1. Basic counts
        print("\n1️⃣ BASIC COUNTS")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN status = 'terminated' THEN 1 END) as terminated
            FROM contracts
        """))
        row = result.fetchone()
        print(f"Total contracts:      {row[0]}")
        print(f"  - Active:           {row[1]}")
        print(f"  - Terminated:       {row[2]}")
        
        # 2. Check for duplicates by unit_id
        print("\n2️⃣ DUPLICATE DETECTION (by unit_id)")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT unit_id, COUNT(*) as contract_count
            FROM contracts
            WHERE unit_id IS NOT NULL
            GROUP BY unit_id
            HAVING COUNT(*) > 1
            ORDER BY contract_count DESC
            LIMIT 10
        """))
        duplicates = result.fetchall()
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} units with multiple contracts:")
            for unit_id, count in duplicates[:10]:
                print(f"  Unit {unit_id}: {count} contracts")
        else:
            print("✅ No duplicate contracts per unit")
        
        # 3. Contracts without units
        print("\n3️⃣ ORPHANED CONTRACTS")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT COUNT(*) FROM contracts WHERE unit_id IS NULL
        """))
        orphaned = result.scalar()
        print(f"Contracts without unit_id: {orphaned}")
        
        # 4. Date range analysis
        print("\n4️⃣ CONTRACT DATE RANGES")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT 
                MIN(start_date) as earliest_start,
                MAX(start_date) as latest_start,
                MIN(end_date) as earliest_end,
                MAX(end_date) as latest_end,
                COUNT(CASE WHEN end_date IS NULL THEN 1 END) as no_end_date
            FROM contracts
        """))
        row = result.fetchone()
        print(f"Start dates: {row[0]} to {row[1]}")
        print(f"End dates:   {row[2]} to {row[3]}")
        print(f"Contracts with no end date: {row[4]}")
        
        # 5. Cost statistics
        print("\n5️⃣ COST STATISTICS")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT 
                COUNT(CASE WHEN amount IS NOT NULL THEN 1 END) as with_amount,
                COUNT(CASE WHEN amount IS NULL THEN 1 END) as without_amount
            FROM contracts
        """))
        row = result.fetchone()
        print(f"Contracts with cost data:    {row[0]}")
        print(f"Contracts without cost data: {row[1]}")
        
        # 6. Party/Landlord distribution
        print("\n6️⃣ LANDLORD DISTRIBUTION")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT 
                p.name,
                COUNT(c.contract_id) as contract_count
            FROM contracts c
            LEFT JOIN parties p ON c.party_id = p.party_id
            GROUP BY p.name
            ORDER BY contract_count DESC
            LIMIT 10
        """))
        landlords = result.fetchall()
        print("Top 10 landlords by contract count:")
        for name, count in landlords:
            landlord_name = name if name else "Unknown/NULL"
            print(f"  {landlord_name:40} {count:4} contracts")
        
        # 7. Regional distribution (via properties)
        print("\n7️⃣ REGIONAL DISTRIBUTION")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT 
                p.region,
                COUNT(c.contract_id) as contract_count
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            WHERE p.region IS NOT NULL
            GROUP BY p.region
            ORDER BY contract_count DESC
        """))
        regions = result.fetchall()
        print("Contracts by region:")
        for region, count in regions:
            print(f"  {region:25} {count:4} contracts")
        
        # 8. Recent import check (created in last 30 days)
        print("\n8️⃣ RECENT IMPORTS")
        print("-" * 70)
        result = await db.execute(text("""
            SELECT 
                DATE(created_at) as import_date,
                COUNT(*) as count
            FROM contracts
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY import_date DESC
        """))
        recent = result.fetchall()
        if recent:
            print("Contracts imported in last 30 days:")
            for date, count in recent:
                print(f"  {date}: {count} contracts")
        else:
            print("No contracts imported in last 30 days")
        
        # 9. Check against CSV
        print("\n9️⃣ CSV COMPARISON")
        print("-" * 70)
        csv_path = "/Volumes/KINGSTON/csv/Bufetat_leiedata_renset.csv"
        try:
            df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
            csv_count = len(df)
            print(f"CSV file has {csv_count} rows")
            print(f"Database has {row[0] if 'row' in locals() else '?'} contracts")
            
            # Count unique addresses in CSV
            unique_addresses = df['Adresselinje 1'].nunique()
            print(f"Unique addresses in CSV: {unique_addresses}")
        except Exception as e:
            print(f"⚠️  Could not read CSV: {e}")
        
        print("\n" + "=" * 70)
        print("✅ AUDIT COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(comprehensive_audit())
