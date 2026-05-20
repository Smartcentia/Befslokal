
import sys
import os
import asyncio
import csv
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from app.domains.core.models.party import Party

async def import_landlords():
    print("Starting Landlord Import from totalny.txt...")
    
    file_path = "docs/totalny.txt"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    async with SessionLocal() as db:
        # 1. Load File Data
        file_map = {} # Property Name -> {name: Utleier, org: OrgNr}
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            for row in reader:
                p_name = row.get("Avtalenavn", "").strip()
                landlord_name = row.get("Utleier", "").strip()
                org_nr = row.get("org nr utleier", "").strip()
                
                # Cleanup OrgNr (remove spaces)
                org_nr = org_nr.replace(" ", "")
                
                if p_name and landlord_name:
                    file_map[p_name.lower()] = {
                        "name": landlord_name,
                        "org": org_nr
                    }
        
        print(f"Loaded landlord data for {len(file_map)} properties.")

        # 2. Pre-fetch Parties (OrgNr -> Party)
        result = await db.execute(select(Party))
        all_parties = result.scalars().all()
        # Map OrgNr -> Party (if OrgNr exists)
        party_org_map = {p.orgnr: p for p in all_parties if p.orgnr}
        # Also Map Name -> Party (fallback if no OrgNr)
        party_name_map = {p.name.lower(): p for p in all_parties if p.name}
        
        # 3. Iterate Contracts
        
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property), joinedload(Contract.party))
        )
        
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        updated_count = 0
        created_parties = 0
        
        for contract in contracts:
            if not contract.unit or not contract.unit.property:
                continue
                
            p_name = contract.unit.property.name.strip().lower()
            landlord_data = file_map.get(p_name)
            
            if not landlord_data:
                continue
                
            l_name = landlord_data["name"]
            l_org = landlord_data["org"]
            
            # Check if current landlord is "Ukjent" OR we want to overwrite?
            # User said "update them". Let's update IF the current one is Ukjent OR if file has specific data and current is mismatched?
            # Safeset: Update if current is Ukjent, or if current has no orgnr but file does.
            
            current_party = contract.party
            is_ukjent = False
            if not current_party:
                is_ukjent = True
            elif "ukjent" in current_party.name.lower():
                is_ukjent = True
            
            # If not Ukjent, maybe we skip? 
            # User context: "oppdater de med data vi nå har". likely implies primarily the missing ones, but effectively improving data.
            # Let's target Ukjent + those where we differ significantly?
            # Let's start with Ukjent to be safe, as requested in previous turn ("how many are unknown" -> "update them")
            
            if not is_ukjent:
                # Optional: Check if we can enrich existing party with OrgNr if missing?
                if current_party and not current_party.orgnr and l_org:
                    print(f"Enriching Party '{current_party.name}' with OrgNr: {l_org}")
                    current_party.orgnr = l_org
                continue

            # Find or Create Target Party
            target_party = None
            
            # Try by OrgNr
            if l_org:
                target_party = party_org_map.get(l_org)
            
            # Try by Name if not found
            if not target_party:
                target_party = party_name_map.get(l_name.lower())
            
            # Create if missing
            if not target_party:
                print(f"Creating New Party: {l_name} (Org: {l_org})")
                target_party = Party(
                    name=l_name,
                    orgnr=l_org,
                    is_landlord=True
                )
                db.add(target_party)
                await db.flush() # Get ID
                
                # Update maps
                if l_org: party_org_map[l_org] = target_party
                party_name_map[l_name.lower()] = target_party
                created_parties += 1
            
            # Link
            if contract.party_id != target_party.party_id:
                old_name = current_party.name if current_party else "None"
                print(f"Updating Contract for '{contract.unit.property.name}': {old_name} -> {target_party.name}")
                contract.party_id = target_party.party_id
                updated_count += 1

        await db.commit()
        print(f"Import Complete.")
        print(f"Contracts Updated: {updated_count}")
        print(f"New Parties Created: {created_parties}")

if __name__ == "__main__":
    asyncio.run(import_landlords())
