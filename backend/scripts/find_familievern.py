#!/usr/bin/env python3
"""Find all familievern (family counseling) contracts"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

async def find_familievern_contracts():
    async with SessionLocal() as db:
        print("=" * 70)
        print("🔍 SEARCHING FOR FAMILIEVERN CONTRACTS")
        print("=" * 70)
        
        # Search for contracts with familievern in property name or address
        result = await db.execute(text("""
            SELECT DISTINCT
                c.contract_id,
                c.status,
                p.name as property_name,
                p.address,
                p.municipality,
                p.region,
                c.start_date,
                c.end_date,
                pa.name as landlord,
                c.amount::text
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE 
                LOWER(p.name) LIKE '%familievern%'
                OR LOWER(p.address) LIKE '%familievern%'
                OR LOWER(CAST(p.usage AS TEXT)) LIKE '%familievern%'
            ORDER BY p.region, p.municipality, p.name
        """))
        
        contracts = result.fetchall()
        
        if not contracts:
            print("\n❌ Ingen familievernkontrakter funnet")
            return
        
        print(f"\n✅ Fant {len(contracts)} familievernkontrakter:\n")
        
        current_region = None
        for contract in contracts:
            contract_id, status, name, address, municipality, region, start, end, landlord, amount = contract
            
            # Print region header if changed
            if region != current_region:
                current_region = region
                print(f"\n{'=' * 70}")
                print(f"Region: {region or 'Ukjent'}")
                print(f"{'=' * 70}")
            
            print(f"\n📍 {name or address}")
            print(f"   Kommune: {municipality or 'Ukjent'}")
            print(f"   Adresse: {address}")
            print(f"   Status: {'Aktiv' if status == 'active' else 'Avsluttet'}")
            print(f"   Periode: {start} til {end or 'Ubestemt'}")
            print(f"   Utleier: {landlord or 'Ukjent'}")
            if amount:
                print(f"   Kontrakt ID: {contract_id}")
        
        # Summary by region
        print("\n" + "=" * 70)
        print("📊 OPPSUMMERING PER REGION")
        print("=" * 70)
        
        result = await db.execute(text("""
            SELECT 
                p.region,
                COUNT(DISTINCT c.contract_id) as contract_count,
                COUNT(DISTINCT p.property_id) as property_count,
                COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_count
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            WHERE 
                LOWER(p.name) LIKE '%familievern%'
                OR LOWER(p.address) LIKE '%familievern%'
                OR LOWER(CAST(p.usage AS TEXT)) LIKE '%familievern%'
            GROUP BY p.region
            ORDER BY contract_count DESC
        """))
        
        summary = result.fetchall()
        for region, total, properties, active in summary:
            print(f"\n{region or 'Ukjent':30} {total:3} kontrakter ({active} aktive) | {properties} eiendommer")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(find_familievern_contracts())
