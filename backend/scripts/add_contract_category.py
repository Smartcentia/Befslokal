
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

async def add_category_column():
    logger.info("Starting migration: Add 'category' column to 'contracts' table")
    
    try:
        async with engine.begin() as conn:
            # Check if column exists
            logger.info("Checking for existing column...")
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='contracts' AND column_name='category'"
            ))
            if result.scalar():
                logger.info("Column 'category' already exists. Skipping.")
                return

            # Add column
            logger.info("Adding column 'category'...")
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN category VARCHAR"))
            # Create index for better performance
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_contracts_category ON contracts (category)"))
            logger.info("Column 'category' added successfully.")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(add_category_column())
    except Exception as e:
        logger.error(f"Migration failed details: {e}")
        sys.exit(1)
