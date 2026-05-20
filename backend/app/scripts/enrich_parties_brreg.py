import asyncio
import sys
import os
from sqlalchemy import select, or_, func

from dotenv import load_dotenv
# Try loading from possible locations
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
load_dotenv(os.path.join(os.getcwd(), '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.party import Party
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.user import User
from app.domains.core.models.audit import AuditLog
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.hms.models.checklist import ChecklistTemplate, ChecklistExecution
from app.models.file_meta import FileMeta
from app.services.external.brreg_service import BrregService
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

async def enrich_parties():
    """
    Finds parties with missing orgnr or name mismatches and resolves them via BRREG.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import engine
    from sqlalchemy.orm import sessionmaker

    # Create a local session factory with expire_on_commit=False to avoid lazy-loading issues in loop
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as db:
        # Get all parties
        stmt = select(Party)
        result = await db.execute(stmt)
        parties = result.scalars().all()
        
        print(f"Inspecting {len(parties)} parties for enrichment or correction.")
        
        updated_count = 0
        for party in parties:
            needs_fix = False
            reason = ""
            
            # Check for missing/placeholder
            if not party.orgnr or party.orgnr in ['', '000000000']:
                needs_fix = True
                reason = "Missing or placeholder orgnr"
            
            # Check for name mismatch or missing source if we have BRREG data
            elif party.external_data:
                brreg_name = party.external_data.get('name') or party.external_data.get('raw_data', {}).get('navn')
                has_source = party.external_data.get('source') is not None
                
                if brreg_name and brreg_name.lower() != party.name.lower():
                    needs_fix = True
                    reason = f"Name mismatch (DB: {party.name}, BRREG: {brreg_name})"
                elif brreg_name and not has_source:
                    needs_fix = True
                    reason = "Missing source marker in external_data"

            if not needs_fix:
                continue

            print(f"Fixing: {party.name} because {reason}...")
            
            # Simple sanitization for searching
            search_name = party.name.replace("(Masterdata)", "").replace("-", " ").strip()
            if "Ukjent Leietaker" in search_name:
                print(f"Skipping generic party: {party.name}")
                continue
                
            results = await BrregService.search_enheter_by_name(search_name, limit=5, db=db)
            
            if not results:
                print(f"No results found for {search_name}")
                continue
                
            # Try to find an exact match or very close match
            match = None
            for res in results:
                if res['name'].lower() == search_name.lower():
                    match = res
                    break
            
            # If no exact match, take the first one if it starts with the name or is very similar
            if not match and results:
                 # Check if the search name is a prefix of or contained in the best result
                 if search_name.lower() in results[0]['name'].lower():
                     match = results[0]
            
            if match:
                print(f"Found match: {match['name']} ({match['orgNr']})")
                
                # Check if this orgnr already exists in another party
                target_orgnr = match['orgNr']
                existing_stmt = select(Party).where(Party.orgnr == target_orgnr, Party.party_id != party.party_id)
                existing_result = await db.execute(existing_stmt)
                existing_party = existing_result.scalar_one_or_none()
                
                if existing_party:
                    print(f"  Conflict: Orgnr {target_orgnr} already used by {existing_party.name}. Merging...")
                    # Pass the contract from this 'party' to 'existing_party'
                    c_stmt = select(Contract).where(Contract.party_id == party.party_id)
                    c_result = await db.execute(c_stmt)
                    contracts = c_result.scalars().all()
                    
                    if contracts:
                        print(f"  Moving {len(contracts)} contracts to {existing_party.name}")
                        for contract in contracts:
                            contract.party_id = existing_party.party_id
                    
                    # Update surviving party with BRREG data
                    new_data = dict(existing_party.external_data or {})
                    new_data["brreg_match"] = match
                    new_data["source"] = match.get("source", "BRREG (Enrichment)")
                    new_data["source_api"] = "bronnoysund"
                    existing_party.external_data = new_data

                    # Delete this redundant party
                    await db.delete(party)
                    updated_count += 1
                else:
                    # Normal update
                    party.orgnr = target_orgnr
                    
                    # Create a new dict copy to ensure SQLAlchemy detects changes
                    new_data = dict(party.external_data or {})
                    new_data["brreg_match"] = match
                    new_data["source"] = match.get("source", "BRREG (Enrichment)")
                    new_data["source_api"] = "bronnoysund"
                    party.external_data = new_data
                    
                    updated_count += 1
                
                # Commit individual change to be safe and clear dirty state
                try:
                    await db.commit()
                except Exception as e:
                    print(f"  Error committing update for {party.name}: {e}")
                    await db.rollback()
            else:
                print(f"No clear match found for {search_name}. Best result: {results[0]['name']}")
        
        print(f"Enrichment completed. Total actions (updates/merges): {updated_count}")

async def merge_duplicate_parties():
    """
    Finds parties with duplicate orgnrs and merges them (contracts and deletions).
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import engine
    from sqlalchemy.orm import sessionmaker

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        # Find orgnrs that appear more than once (excluding null/placeholder)
        stmt = select(Party.orgnr).where(
            Party.orgnr != None,
            Party.orgnr != '',
            Party.orgnr != '000000000'
        ).group_by(Party.orgnr).having(func.count(Party.orgnr) > 1)
        
        result = await db.execute(stmt)
        duplicate_orgnrs = result.scalars().all()
        
        if not duplicate_orgnrs:
            print("No duplicate orgnrs found to merge.")
            return

        print(f"Found {len(duplicate_orgnrs)} duplicate organization numbers. Merging...")
        
        for orgnr in duplicate_orgnrs:
            # Get all parties with this orgnr
            p_stmt = select(Party).where(Party.orgnr == orgnr).order_by(Party.created_at.asc())
            p_result = await db.execute(p_stmt)
            parties = p_result.scalars().all()
            
            # Keep the oldest one as primary
            primary = parties[0]
            duplicates = parties[1:]
            
            print(f"Merging {len(duplicates)} duplicates into primary: {primary.name} ({primary.orgnr})")
            
            for dupe in duplicates:
                # 1. Update all contracts to point to primary
                c_stmt = select(Contract).where(Contract.party_id == dupe.party_id)
                c_result = await db.execute(c_stmt)
                contracts = c_result.scalars().all()
                
                if contracts:
                    print(f"  Moving {len(contracts)} contracts from {dupe.party_id} to {primary.party_id}")
                    for contract in contracts:
                        contract.party_id = primary.party_id
                
                # 2. Delete the duplicate party
                await db.delete(dupe)
            
        await db.commit()
        print("Successfully merged duplicate parties.")

async def check_contracts_parties():
    """
    Check all contracts and report missing party/orgnr info.
    """
    from sqlalchemy.orm import selectinload
    
    async with SessionLocal() as db:
        stmt = select(Contract).options(selectinload(Contract.party))
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        print(f"\nChecking {len(contracts)} contracts...")
        total_missing = 0
        for c in contracts:
            party_name = c.party.name if c.party else "NO PARTY LINKED"
            orgnr = c.party.orgnr if c.party else "N/A"
            
            if not c.party or not orgnr or orgnr == '000000000':
                print(f"Contract {c.contract_id}: Missing Orgnr for party '{party_name}'")
                total_missing += 1
        
        print(f"Total contracts with missing/default orgnr: {total_missing}")

async def main():
    print("=== BEFS Party Enrichment Utility ===")
    await merge_duplicate_parties()
    await enrich_parties()
    await check_contracts_parties()

if __name__ == "__main__":
    asyncio.run(main())
