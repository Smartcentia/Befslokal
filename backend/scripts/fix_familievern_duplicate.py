#!/usr/bin/env python3
"""Fix duplicate familievern contracts"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

async def analyze_and_fix_duplicates():
    async with SessionLocal() as db:
        print("=" * 70)
        print("🔍 ANALYSE AV FAMILIEVERN DUPLIKATER")
        print("=" * 70)
        
        # Get detailed info about both contracts
        result = await db.execute(text("""
            SELECT 
                c.contract_id,
                c.status,
                c.start_date,
                c.end_date,
                c.created_at,
                c.amount::text,
                c.party_id,
                pa.name as landlord,
                p.name as property_name,
                p.address
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE LOWER(p.name) LIKE '%familievern%'
            ORDER BY c.created_at
        """))
        
        contracts = result.fetchall()
        
        print(f"\nFant {len(contracts)} kontrakter for FVK Bodø:\n")
        
        for idx, contract in enumerate(contracts, 1):
            cid, status, start, end, created, amount, party_id, landlord, prop, addr = contract
            print(f"\nKONTRAKT {idx}:")
            print(f"  ID: {cid}")
            print(f"  Opprettet: {created}")
            print(f"  Periode: {start} til {end}")
            print(f"  Status: {status}")
            print(f"  Utleier: {landlord if party_id else '⚠️  MANGLER'}")
            print(f"  Party ID: {party_id or 'NULL'}")
            print(f"  Beløp: {amount[:100] if amount else 'Ingen'}...")
        
        # Recommendation
        print(f"\n\n{'=' * 70}")
        print("💡 ANBEFALING")
        print(f"{'=' * 70}")
        
        if len(contracts) == 2:
            # Check which one has landlord
            with_landlord = [c for c in contracts if c[6] is not None]
            without_landlord = [c for c in contracts if c[6] is None]
            
            if len(without_landlord) == 1 and len(with_landlord) == 1:
                print("\n✅ Klar duplikatsituasjon:")
                print(f"   - Kontrakt MED utleier: {with_landlord[0][0]}")
                print(f"   - Kontrakt UTEN utleier: {without_landlord[0][0]}")
                print("\n📋 Foreslått handling:")
                print(f"   SLETT kontrakt uten utleier: {without_landlord[0][0]}")
                print(f"   BEHOLD kontrakt med utleier: {with_landlord[0][0]}")
                
                print("\n⚠️  SQL for å slette duplikat:")
                print(f"   DELETE FROM contracts WHERE contract_id = '{without_landlord[0][0]}';")
            else:
                print("\n⚠️  Begge kontrakter har samme utleierstatus")
                print("   Manuell gjennomgang anbefales")
        
        # Check if they're truly identical
        print(f"\n\n{'=' * 70}")
        print("🔬 SAMMENLIGNING")
        print(f"{'=' * 70}")
        
        if len(contracts) == 2:
            c1, c2 = contracts
            print(f"\nSammenligner kontrakt 1 og 2:")
            print(f"  Samme startdato: {'✅' if c1[2] == c2[2] else '❌'} ({c1[2]} vs {c2[2]})")
            print(f"  Samme sluttdato: {'✅' if c1[3] == c2[3] else '❌'} ({c1[3]} vs {c2[3]})")
            print(f"  Samme status: {'✅' if c1[1] == c2[1] else '❌'} ({c1[1]} vs {c2[1]})")
            print(f"  Begge har utleier: {'❌ NEI' if (c1[6] is None or c2[6] is None) else '✅ JA'}")

if __name__ == "__main__":
    asyncio.run(analyze_and_fix_duplicates())
