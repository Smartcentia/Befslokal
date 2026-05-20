"""
Apply database schema changes for text_content table.
Adds full-text search support and vector search migration fields.
"""

import os
import sys
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from sqlalchemy import text
from app.db.session import engine
from app.services.logger import get_logger

logger = get_logger(__name__)


async def apply_schema_changes():
    """Apply schema changes to text_content table."""
    
    logger.info("Applying schema changes to text_content table...")
    
    async with engine.begin() as conn:
        # Add new columns
        alterations = [
            # Vector search migration fields
            "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS source_index_id VARCHAR(255) UNIQUE",
            "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS source_file VARCHAR(500)",
            "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS chunk_index INTEGER DEFAULT 0",
            "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
            
            # Change content to TEXT type for large documents
            "ALTER TABLE text_content ALTER COLUMN content TYPE TEXT",
            
            # Full-text search support
            "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS search_vector TSVECTOR",
            
            # Updated timestamp
            "ALTER TABLE text_content ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        ]
        
        for sql in alterations:
            try:
                logger.info(f"Executing: {sql[:80]}...")
                await conn.execute(text(sql))
                logger.info("  ✓ Success")
            except Exception as e:
                logger.warning(f"  ⚠️  {e} (might already exist)")
        
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
        
        # Create trigger for automatic search_vector updates
        trigger_function = """
        CREATE OR REPLACE FUNCTION text_content_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('norwegian', COALESCE(NEW.content, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
        
        trigger_sql = """
        DROP TRIGGER IF EXISTS text_content_search_vector_trigger ON text_content;
        CREATE TRIGGER text_content_search_vector_trigger
        BEFORE INSERT OR UPDATE ON text_content
        FOR EACH ROW EXECUTE FUNCTION text_content_search_vector_update();
        """
        
        try:
            logger.info("Creating search_vector update trigger...")
            await conn.execute(text(trigger_function))
            await conn.execute(text(trigger_sql))
            logger.info("  ✓ Trigger created successfully")
        except Exception as e:
            logger.warning(f"  ⚠️  {e}")
    
    logger.info("Schema changes applied successfully!")


if __name__ == "__main__":
    asyncio.run(apply_schema_changes())
