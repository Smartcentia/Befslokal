#!/usr/bin/env python3
"""
Quick statistics about properties and synthetic data.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models
import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from sqlalchemy import select, text

async def quick_stats():
    """Show quick statistics."""
    async with SessionLocal() as db:
        # Total properties
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        total_props = len(properties)
        
        # Properties with financial_history
        stmt = text("""
            SELECT COUNT(*) 
            FROM properties 
            WHERE external_data->'financial_history' IS NOT NULL
        """)
        result = await db.execute(stmt)
        with_history = result.scalar()
        
        # Properties with GL transactions
        stmt = text("""
            SELECT COUNT(DISTINCT property_id) 
            FROM gl_transactions
        """)
        result = await db.execute(stmt)
        with_gl = result.scalar()
        
        # Total GL transactions
        stmt = text("SELECT COUNT(*) FROM gl_transactions")
        result = await db.execute(stmt)
        total_gl = result.scalar()
        
        print("=" * 60)
        print("📊 Quick Statistics")
        print("=" * 60)
        print(f"\nTotal properties: {total_props}")
        print(f"Properties with financial_history: {with_history} ({with_history/total_props*100:.1f}%)")
        print(f"Properties with GL transactions: {with_gl} ({with_gl/total_props*100:.1f}%)")
        print(f"Total GL transactions: {total_gl:,}")
        
        if total_props > 0:
            expected_transactions = total_props * 36 * 4  # 36 months × 4 transaction types
            print(f"Expected transactions (if all complete): {expected_transactions:,}")
            print(f"Current coverage: {total_gl/expected_transactions*100:.1f}%")
        
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(quick_stats())
