#!/usr/bin/env python3
"""
Clean up contracts with corrupted amounts (> 50M NOK threshold).
Sets erroneous amounts to NULL for manual correction.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select, update
from sqlalchemy.orm.attributes import flag_modified

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

THRESHOLD = 50_000_000  # 50 Million NOK

async def cleanup_bad_amounts():
    print("🧹 Cleaning up corrupted contract amounts...")
    print(f"Threshold: {THRESHOLD:,} NOK")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Find contracts with suspiciously high amounts
        result = await db.execute(select(Contract))
        contracts = result.scalars().all()
        
        bad_contracts = []
        
        for c in contracts:
            if not c.amount:
                continue
            amt = c.amount.get('amount_per_year')
            if amt and amt > THRESHOLD:
                bad_contracts.append({
                    'id': c.contract_id,
                    'amount': amt,
                    'unit_id': c.unit_id
                })
        
        print(f"\nFound {len(bad_contracts)} contracts with amount > {THRESHOLD:,} NOK")
        
        if not bad_contracts:
            print("✅ No corrupted amounts found.")
            return
        
        print("\n📋 Contracts to be cleaned:")
        for bc in bad_contracts:
            print(f"  - Contract {bc['id']}: {bc['amount']:,.0f} NOK")
        
        # Set amounts to None - CRITICAL: use flag_modified for JSONB fields
        for bc in bad_contracts:
            contract = await db.get(Contract, bc['id'])
            if contract and contract.amount:
                contract.amount['amount_per_year'] = None
                # Mark the JSONB field as modified so SQLAlchemy knows to update it
                flag_modified(contract, 'amount')
        
        await db.commit()
        
        print(f"\n✅ Set {len(bad_contracts)} contract amounts to NULL")
        print("\n⚠️  ACTION REQUIRED:")
        print("   These contracts need manual correction from source documents.")
        print(f"   Contract IDs: {[str(bc['id']) for bc in bad_contracts]}")

if __name__ == "__main__":
    asyncio.run(cleanup_bad_amounts())
