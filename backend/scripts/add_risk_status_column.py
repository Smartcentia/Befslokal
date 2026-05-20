"""
Add missing status column to risk_assessments.
"""

import os
import sys
import asyncio

# Fix path to include backend root
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from sqlalchemy import text
from app.db.session import engine
import logging

# Configure logging locally since app.services.logger might need config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_status_column():
    logger.info("Adding missing status column to risk_assessments...")
    
    async with engine.begin() as conn:
        try:
            # Check if column exists first (Postgres specific check or just IF NOT EXISTS)
            # Using IF NOT EXISTS directly in ALTER TABLE is supported in recent Postgres
            
            await conn.execute(text("ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'OPEN' NOT NULL"))
            logger.info("  ✓ Column 'status' added successfully")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(add_status_column())
