"""
Test single document migration to see full error.
"""

import os
import sys
import asyncio
import json
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from sqlalchemy import text
from app.db.session import engine
from app.services.logger import get_logger

logger = get_logger(__name__)


async def test_insert():
    """Test inserting a single dummy document."""
    
    async with engine.connect() as conn:
        async with conn.begin():
            insert_sql = text("""
                INSERT INTO text_content (
                    text_id, source_index_id, source_type, content, source_file,
                    category, chunk_index, additional_metadata
                ) VALUES (
                    :text_id, :source_index_id, :source_type, :content, :source_file,
                    :category, :chunk_index, :metadata
                )
            """)
            
            try:
                await conn.execute(insert_sql, {
                    'text_id': str(uuid.uuid4()),
                    'source_index_id': 'test_id_123',
                    'source_type': 'test',
                    'content': 'Test content',
                    'source_file': 'test.pdf',
                    'category': 'test_category',
                    'chunk_index': 0,
                    'metadata': json.dumps({'test': 'value'})
                })
                logger.info("✅ Insert successful!")
            except Exception as e:
                logger.error(f"❌ Insert failed: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_insert())
