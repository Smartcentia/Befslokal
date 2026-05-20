#!/usr/bin/env python3
"""Quick database contract count check"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import select, func

# Import all models to register relationships
import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.audit

from app.domains.core.models.contract import Contract

async def check_counts():
    async with SessionLocal() as db:
        from sqlalchemy import text
        
        # Total contracts
        result = await db.execute(text("SELECT COUNT(*) FROM contracts"))
        total = result.scalar()
        
        # Active contracts
        result = await db.execute(text("SELECT COUNT(*) FROM contracts WHERE status = 'active'"))
        active = result.scalar()
        
        # Terminated contracts
        result = await db.execute(text("SELECT COUNT(*) FROM contracts WHERE status = 'terminated'"))
        terminated = result.scalar()
        
        print(f"📊 Contract Database Status:")
        print(f"  Total contracts: {total}")
        print(f"  Active: {active}")
        print(f"  Terminated: {terminated}")

if __name__ == "__main__":
    asyncio.run(check_counts())
