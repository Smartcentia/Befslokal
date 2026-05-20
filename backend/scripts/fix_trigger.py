"""
Fix trigger creation with separate statements.
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


async def fix_trigger():
    """Create trigger with separate statements."""
    
    logger.info("Creating search_vector update trigger...")
    
    async with engine.begin() as conn:
        # Drop existing trigger first
        try:
            await conn.execute(text("DROP TRIGGER IF EXISTS text_content_search_vector_trigger ON text_content"))
            logger.info("  ✓ Dropped existing trigger")
        except Exception as e:
            logger.warning(f"  ⚠️  {e}")
        
        # Create trigger function
        trigger_function = """
        CREATE OR REPLACE FUNCTION text_content_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('norwegian', COALESCE(NEW.content, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql
        """
        
        try:
            await conn.execute(text(trigger_function))
            logger.info("  ✓ Created trigger function")
        except Exception as e:
            logger.error(f"  ✗ Failed to create function: {e}")
            return
        
        # Create trigger
        trigger_sql = """
        CREATE TRIGGER text_content_search_vector_trigger
        BEFORE INSERT OR UPDATE ON text_content
        FOR EACH ROW EXECUTE FUNCTION text_content_search_vector_update()
        """
        
        try:
            await conn.execute(text(trigger_sql))
            logger.info("  ✓ Created trigger successfully")
        except Exception as e:
            logger.error(f"  ✗ Failed to create trigger: {e}")
    
    logger.info("Trigger setup complete!")


if __name__ == "__main__":
    asyncio.run(fix_trigger())
