#!/usr/bin/env python3
"""Search for all types of Bufetat facilities"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

async def find_all_bufetat_facilities():
    async with SessionLocal() as db:
        print("=" * 70)
        print("🏛️  ALLE BUFETAT-KONTOR OG INSTITUSJONER")
        print("=" * 70)
        
        # Search terms for different facility types
        search_terms = [
            ('Familievern', '%familievern%'),
            ('Barnevern', '%barnevern%'),
            ('BUP', '%bup%'),
            ('Bufdir', '%bufdir%'),
            ('Bufetat', '%bufetat%'),
            ('Statens barnehus', '%barnehus%'),
            ('Omsorgssenter', '%omsorg%'),
            ('Institusjon', '%institusjon%'),
        ]
        
        all_results = {}
        
        for facility_type, pattern in search_terms:
            result = await db.execute(text(f"""
                SELECT DISTINCT
                    p.property_id,
                    p.name,
                    p.address,
                    p.municipality,
                    p.region,
                    p.usage,
                    COUNT(c.contract_id) as contract_count,
                    COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_count
                FROM properties p
                LEFT JOIN units u ON p.property_id = u.property_id
                LEFT JOIN contracts c ON u.unit_id = c.unit_id
                WHERE 
                    LOWER(p.name) LIKE :pattern
                    OR LOWER(p.address) LIKE :pattern
                    OR LOWER(CAST(p.usage AS TEXT)) LIKE :pattern
                GROUP BY p.property_id, p.name, p.address, p.municipality, p.region, p.usage
                ORDER BY p.region, p.municipality, p.name
            """), {"pattern": pattern})
            
            facilities = result.fetchall()
            if facilities:
                all_results[facility_type] = facilities
        
        # Print results by type
        total_facilities = 0
        total_contracts = 0
        
        for facility_type, facilities in all_results.items():
            print(f"\n{'=' * 70}")
            print(f"📍 {facility_type.upper()}")
            print(f"{'=' * 70}")
            print(f"Antall: {len(facilities)} eiendommer\n")
            
            current_region = None
            for facility in facilities:
                prop_id, name, address, municipality, region, usage, contracts, active = facility
                
                if region != current_region:
                    current_region = region
                    print(f"\n--- {region or 'Ukjent region'} ---")
                
                print(f"\n  • {name or address}")
                print(f"    {address}")
                print(f"    {municipality or 'Ukjent kommune'}")
                if contracts > 0:
                    print(f"    Kontrakter: {contracts} ({active} aktive)")
                if usage:
                    print(f"    Bruk: {usage}")
            
            total_facilities += len(facilities)
            total_contracts += sum(f[6] for f in facilities)
        
        # Summary
        print(f"\n\n{'=' * 70}")
        print("📊 OPPSUMMERING")
        print(f"{'=' * 70}")
        
        for facility_type, facilities in sorted(all_results.items(), key=lambda x: len(x[1]), reverse=True):
            contract_count = sum(f[6] for f in facilities)
            active_count = sum(f[7] for f in facilities)
            print(f"\n{facility_type:25} {len(facilities):3} eiendommer | {contract_count:3} kontrakter ({active_count} aktive)")
        
        print(f"\n{'=' * 70}")
        print(f"TOTALT: {total_facilities} eiendommer | {total_contracts} kontrakter")
        print(f"{'=' * 70}")
        
        # Regional distribution
        print(f"\n\n{'=' * 70}")
        print("🗺️  REGIONAL FORDELING")
        print(f"{'=' * 70}")
        
        result = await db.execute(text("""
            SELECT 
                p.region,
                COUNT(DISTINCT p.property_id) as property_count,
                COUNT(c.contract_id) as contract_count
            FROM properties p
            LEFT JOIN units u ON p.property_id = u.property_id
            LEFT JOIN contracts c ON u.unit_id = c.unit_id
            WHERE 
                LOWER(p.name) LIKE '%familievern%'
                OR LOWER(p.name) LIKE '%barnevern%'
                OR LOWER(p.name) LIKE '%bup%'
                OR LOWER(p.name) LIKE '%bufdir%'
                OR LOWER(p.name) LIKE '%bufetat%'
                OR LOWER(p.name) LIKE '%barnehus%'
            GROUP BY p.region
            ORDER BY contract_count DESC
        """))
        
        regions = result.fetchall()
        for region, props, contracts in regions:
            print(f"\n{region or 'Ukjent':30} {props:3} eiendommer | {contracts:3} kontrakter")

if __name__ == "__main__":
    asyncio.run(find_all_bufetat_facilities())
