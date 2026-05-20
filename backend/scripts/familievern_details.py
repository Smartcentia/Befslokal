#!/usr/bin/env python3
"""Get detailed information about familievern contracts"""
import asyncio
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

async def get_familievern_details():
    async with SessionLocal() as db:
        print("=" * 70)
        print("📋 DETALJERT INFORMASJON - FAMILIEVERN KONTRAKTER")
        print("=" * 70)
        
        result = await db.execute(text("""
            SELECT 
                c.contract_id,
                c.status,
                c.category,
                c.start_date,
                c.end_date,
                c.amount::text as amount_json,
                c.caretaker_cost,
                c.cleaning_cost,
                c.parking_cost,
                c.card_reader_cost,
                c.external_data::text as external_data_json,
                c.created_at,
                p.property_id,
                p.name as property_name,
                p.address,
                p.municipality,
                p.region,
                p.total_area,
                p.approved_places,
                p.usage,
                pa.party_id,
                pa.name as landlord_name,
                pa.org_number,
                u.unit_id
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE 
                LOWER(p.name) LIKE '%familievern%'
                OR LOWER(p.address) LIKE '%familievern%'
            ORDER BY c.created_at DESC
        """))
        
        contracts = result.fetchall()
        
        for idx, contract in enumerate(contracts, 1):
            print(f"\n{'=' * 70}")
            print(f"KONTRAKT {idx} av {len(contracts)}")
            print(f"{'=' * 70}")
            
            (contract_id, status, category, start, end, amount_json, caretaker, 
             cleaning, parking, card, external_json, created, prop_id, prop_name,
             address, municipality, region, area, places, usage, party_id, 
             landlord, org_num, unit_id) = contract
            
            print(f"\n🏢 EIENDOMSINFORMASJON")
            print(f"   Navn: {prop_name}")
            print(f"   Adresse: {address}")
            print(f"   Kommune: {municipality}")
            print(f"   Region: {region}")
            print(f"   Areal: {area} m²" if area else "   Areal: Ikke oppgitt")
            print(f"   Godkjente plasser: {places}" if places else "   Godkjente plasser: Ikke oppgitt")
            print(f"   Bruk: {usage}" if usage else "   Bruk: Ikke oppgitt")
            print(f"   Property ID: {prop_id}")
            
            print(f"\n📄 KONTRAKTSINFORMASJON")
            print(f"   Kontrakt ID: {contract_id}")
            print(f"   Unit ID: {unit_id}")
            print(f"   Status: {'Aktiv' if status == 'active' else 'Avsluttet'}")
            print(f"   Kategori: {category}" if category else "   Kategori: Ikke oppgitt")
            print(f"   Startdato: {start}")
            print(f"   Sluttdato: {end or 'Ubestemt'}")
            print(f"   Opprettet i database: {created}")
            
            print(f"\n👤 UTLEIER")
            if party_id:
                print(f"   Navn: {landlord}")
                print(f"   Org.nr: {org_num}" if org_num else "   Org.nr: Ikke oppgitt")
                print(f"   Party ID: {party_id}")
            else:
                print(f"   ⚠️  INGEN UTLEIER REGISTRERT")
            
            print(f"\n💰 KOSTNADER")
            if amount_json:
                try:
                    amount_data = json.loads(amount_json)
                    print(f"   Beløpsdata: {json.dumps(amount_data, indent=6, ensure_ascii=False)}")
                except:
                    print(f"   Beløpsdata (raw): {amount_json}")
            else:
                print(f"   Ingen beløpsdata")
            
            if caretaker:
                print(f"   Vaktmester: {caretaker:,.2f} kr")
            if cleaning:
                print(f"   Renhold: {cleaning:,.2f} kr")
            if parking:
                print(f"   Parkering: {parking:,.2f} kr")
            if card:
                print(f"   Kortleser: {card:,.2f} kr")
            
            if external_json:
                print(f"\n📊 EKSTERNE DATA (fra CSV)")
                try:
                    ext_data = json.loads(external_json)
                    for key, value in ext_data.items():
                        if value:
                            print(f"   {key}: {value}")
                except:
                    print(f"   {external_json}")
        
        # Check for duplicates
        print(f"\n\n{'=' * 70}")
        print("🔍 DUPLIKATANALYSE")
        print(f"{'=' * 70}")
        
        result = await db.execute(text("""
            SELECT 
                p.property_id,
                p.name,
                p.address,
                COUNT(c.contract_id) as contract_count,
                STRING_AGG(c.contract_id::text, ', ') as contract_ids,
                STRING_AGG(pa.name, ' | ') as landlords
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE 
                LOWER(p.name) LIKE '%familievern%'
            GROUP BY p.property_id, p.name, p.address
            HAVING COUNT(c.contract_id) > 1
        """))
        
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"\n⚠️  Fant {len(duplicates)} eiendom(mer) med flere kontrakter:")
            for prop_id, name, addr, count, ids, landlords in duplicates:
                print(f"\n   Eiendom: {name} ({addr})")
                print(f"   Antall kontrakter: {count}")
                print(f"   Kontrakt IDer: {ids}")
                print(f"   Utleiere: {landlords}")
        else:
            print("\n✅ Ingen duplikater funnet")

if __name__ == "__main__":
    asyncio.run(get_familievern_details())
