#!/usr/bin/env python3
"""
Update expired contracts to 'terminated' status.
"""
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime
from sqlalchemy import select

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

async def update_expired_contracts():
    print("📅 Updating expired contracts to 'terminated' status...")
    print("=" * 60)
    
    today = datetime.now().date()
    
    async with SessionLocal() as db:
        # Find active contracts that have expired
        result = await db.execute(
            select(Contract).where(Contract.status == 'active')
        )
        contracts = result.scalars().all()
        
        expired = []
        
        for c in contracts:
            if c.end_date:
                # Handle both datetime and date objects
                end_date = c.end_date
                if isinstance(end_date, datetime):
                    end_date = end_date.date()
                
                if end_date < today:
                    expired.append(c)
        
        print(f"\nFound {len(expired)} expired contracts still marked as 'active'")
        
        if not expired:
            print("✅ No expired active contracts found.")
            return
        
        print("\n📋 Updating contracts:")
        for c in expired[:5]:  # Show first 5 examples
            print(f"  - Contract {c.contract_id}: ended {c.end_date}")
        if len(expired) > 5:
            print(f"  ... and {len(expired) - 5} more")
        
        # Update status
        for c in expired:
            c.status = 'terminated'
        
        await db.commit()
        
        print(f"\n✅ Updated {len(expired)} contracts to 'terminated' status")

if __name__ == "__main__":
    asyncio.run(update_expired_contracts())
