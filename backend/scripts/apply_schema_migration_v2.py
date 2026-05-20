"""
Apply database schema changes with explicit commit verification.
"""

import os
import sys
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from sqlalchemy import text
from app.db.session import engine
from app.services.logger import get_logger

logger = get_logger(__name__)


async def apply_schema_changes():
    """Apply schema changes to text_content table with verification."""
    
    logger.info("Applying schema changes to text_content table...")
    
    # Use connect() instead of begin() for manual transaction control
    async with engine.connect() as conn:
        async with conn.begin():
            # Add new columns
            alterations = [
                "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS source_index_id VARCHAR(255)",
                "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS source_file VARCHAR(500)",
                "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS chunk_index INTEGER DEFAULT 0",
                "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
                "ALTER TABLE text_content ALTER COLUMN content TYPE TEXT",
                "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS search_vector TSVECTOR",
                "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
            ]
            
            for sql in alterations:
                try:
                    logger.info(f"Executing: {sql[:80]}...")
                    await conn.execute(text(sql))
                    logger.info("  ✓ Success")
                except Exception as e:
                    logger.error(f"  ✗ Failed: {e}")
                    raise
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_text_content_search_vector ON text_content USING GIN(search_vector)",
                "CREATE INDEX IF NOT EXISTS idx_text_content_source_index_id ON text_content(source_index_id)",
                "CREATE INDEX IF NOT EXISTS idx_text_content_contract_id ON text_content(contract_id)",
            ]
            
            for sql in indexes:
                try:
                    logger.info(f"Executing: {sql[:80]}...")
                    await conn.execute(text(sql))
                    logger.info("  ✓ Success")
                except Exception as e:
                    logger.warning(f"  ⚠️  {e}")
            
            logger.info("Committing transaction...")
        
        logger.info("Transaction committed successfully!")
    
    # Verify columns were created
    logger.info("\nVerifying schema changes...")
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'text_content' ORDER BY ordinal_position"
        ))
        columns = [row[0] for row in result]
        logger.info(f"Current columns: {', '.join(columns)}")
        
        required_columns = ['source_index_id', 'source_file', 'chunk_index', 'category', 'search_vector', 'updated_at']
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            logger.error(f"❌ Missing columns: {', '.join(missing)}")
            return False
        else:
            logger.info("✅ All required columns present!")
            return True


if __name__ == "__main__":
    success = asyncio.run(apply_schema_changes())
    sys.exit(0 if success else 1)
