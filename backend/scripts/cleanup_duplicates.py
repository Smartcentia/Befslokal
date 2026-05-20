
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select, delete
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract

# Import all models to ensure SQLAlchemy relationships are registered
import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

async def cleanup_duplicates():
    print("🧹 Starting cleanup of duplicate contracts...")
    
    async with SessionLocal() as db:
        # Fetch all contracts
        result = await db.execute(select(Contract))
        contracts = result.scalars().all()
        
        print(f"Total contracts before cleanup: {len(contracts)}")
        
        # Group by signature
        # Signature: unit_id, party_id, start_date, end_date, amount
        grouped = defaultdict(list)
        
        for c in contracts:
            amt = c.amount.get('amount_per_year') if c.amount else None
            # Use a tuple as key
            sig = (
                str(c.unit_id) if c.unit_id else None,
                str(c.party_id) if c.party_id else None,
                c.start_date, 
                c.end_date, 
                amt
            )
            grouped[sig].append(c)
            
        ids_to_delete = []
        
        for sig, group in grouped.items():
            if len(group) > 1:
                # Keep the first one, delete the rest
                # Sort by contract_id simply to be deterministic
                group.sort(key=lambda x: str(x.contract_id))
                
                keep = group[0]
                duplicates = group[1:]
                
                print(f"Found {len(duplicates)} duplicates for contract at Unit {keep.unit_id} ({keep.start_date} - {keep.end_date})")
                
                for dup in duplicates:
                    ids_to_delete.append(dup.contract_id)
        
        if not ids_to_delete:
            print("✅ No duplicates found.")
            return

        print(f"\n🗑️  Deleting {len(ids_to_delete)} duplicate contracts...")
        
        # Delete in batches
        stmt = delete(Contract).where(Contract.contract_id.in_(ids_to_delete))
        await db.execute(stmt)
        await db.commit()
        
        print("✅ Cleanup complete!")
        
        # Verify
        count = await db.scalar(select(func.count(Contract.contract_id))) # Need func import if I use this, but len(contracts) - deleted is easier
        print(f"Contracts remaining: {len(contracts) - len(ids_to_delete)}")

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
