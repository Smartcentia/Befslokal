"""
Add missing additional_metadata column.
"""

import os
import sys
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from sqlalchemy import text
from app.db.session import engine
from app.services.logger import get_logger

logger = get_logger(__name__)

async def add_missing_column():
    logger.info("Adding missing additional_metadata column...")
    
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE text_content ADD COLUMN IF NOT EXISTS additional_metadata JSON"))
            logger.info("  ✓ Column added successfully")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(add_missing_column())
