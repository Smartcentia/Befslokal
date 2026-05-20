
import asyncio
import sys
import os
import json
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload

# Add backend root to path
sys.path.append(os.getcwd())

from app.db import base # Import all models to ensure relationships resolve
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party

# Helper for address normalization (simple version for this fix)
def normalize_address(addr):
    if not addr: return ""
    return " ".join(addr.lower().replace(",", "").split())

async def fix_financials(dry_run=True):
    print(f"--- FIX FINANCIAL DATA MIX-UP ({'DRY RUN' if dry_run else 'LIVE'}) ---")
    
    async with SessionLocal() as db:
        # 1. Fetch "Fake" Contracts
        # We identify them by having 'financials' key in external_data
        stmt = select(Contract).options(
            selectinload(Contract.unit).selectinload(Unit.property)
        )
        result = await db.execute(stmt)
        all_contracts = result.scalars().all()
        
        fake_contracts = []
        for c in all_contracts:
            ext = c.external_data or {}
            if isinstance(ext, dict) and ('financials' in ext or 'transaction_count' in str(ext)):
                fake_contracts.append(c)
        
        print(f"Found {len(fake_contracts)} contracts with financial data.")
        
        updated_properties = 0
        deleted_contracts = 0
        skipped = 0
        
        for contract in fake_contracts:
            financial_data = contract.external_data.get('financials')
            if not financial_data:
                # Fallback if structure is slightly different (e.g. at root)
                # content of external_data IS the financial data
                financial_data = contract.external_data
            
            # Find Target Property
            target_property = None
            
            # Strategy A: Via Unit
            if contract.unit and contract.unit.property:
                target_property = contract.unit.property
                match_method = "Linked Unit"
            
            # Strategy B: Address Match (if A fails)
            if not target_property:
                # Extract address from financial data
                # Based on inspection: 'dim_2_original': 'Tærudgata 16, 2004 Lillestrøm'
                addr_str = financial_data.get('dim_2_original')
                if addr_str:
                    # Try to match with existing properties
                    # This is expensive but fine for a one-off 300 item script
                    norm_addr = normalize_address(addr_str)
                    
                    # Fetch all properties if not already cached (could optimize, but keep simple)
                    prop_res = await db.execute(select(Property))
                    all_props = prop_res.scalars().all()
                    
                    for p in all_props:
                        if p.address and normalize_address(p.address) in norm_addr:
                            target_property = p
                            match_method = "Address Match"
                            break
            
            if target_property:
                # Update Property
                prop_ext = dict(target_property.external_data or {}) # Ensure dict copy
                
                # Merge financials. We don't want to overwrite existing if it's already there?
                # Assumption: The data in contracts is the "new" imported data we wanted.
                # Let's populate 'financials' key.
                prop_ext['financials'] = financial_data
                
                if not dry_run:
                    target_property.external_data = prop_ext
                    # Delete Contract
                    await db.delete(contract)
                
                updated_properties += 1
                deleted_contracts += 1
                print(f"✓ [{match_method}] Moved financials from Contract {str(contract.contract_id)[:8]}... to Property {target_property.address}")
                
            else:
                print(f"⚠️  Could not find property for Contract {str(contract.contract_id)[:8]}... (Data: {str(financial_data)[:50]}...)")
                skipped += 1
        
        print("-" * 30)
        print(f"Summary:")
        print(f"To be Updated/Deleted: {updated_properties}")
        print(f"Skipped (No Property Match): {skipped}")
        
        if not dry_run:
            await db.commit()
            print("committed changes.")
        else:
            await db.rollback()
            print("Rolled back (Dry Run).")

if __name__ == "__main__":
    is_dry = "--live" not in sys.argv
    asyncio.run(fix_financials(dry_run=is_dry))
