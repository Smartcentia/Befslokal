
import asyncio
import logging
import os
import sys

# Ensure app can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from sqlalchemy import text
from app.db.session import engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

async def add_region_column():
    logger.info("Starting migration: Add 'region' column to 'properties' table")
    
    try:
        async with engine.begin() as conn:
            # Check if column exists
            logger.info("Checking for existing column...")
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='properties' AND column_name='region'"
            ))
            if result.scalar():
                logger.info("Column 'region' already exists. Skipping.")
                return

            # Add column
            logger.info("Adding column 'region'...")
            await conn.execute(text("ALTER TABLE properties ADD COLUMN region VARCHAR"))
            logger.info("Column 'region' added successfully.")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(add_region_column())
    except Exception as e:
        logger.error(f"Migration failed details: {e}")
        sys.exit(1)
