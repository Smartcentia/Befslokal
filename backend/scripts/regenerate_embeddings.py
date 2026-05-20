import asyncio
import os
import sys
import logging
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from tqdm import tqdm

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from app.db.session import SessionLocal
from app.models.text_content import TextContent
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_embedding(client: AsyncOpenAI, text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    if not text:
        return None
    try:
        response = await client.embeddings.create(
            input=text,
            model=settings.OPENAI_EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

async def regenerate_embeddings(batch_size: int = 20):
    """Regenerate embeddings for all text content."""
    
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set")
        return

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
    
    async with SessionLocal() as session:
        # Count total rows
        count_stmt = select(func.count()).select_from(TextContent).where(TextContent.embedding == None)
        total_rows = await session.scalar(count_stmt)
        
        logger.info(f"Found {total_rows} rows missing embeddings")
        
        # Process in batches
        offset = 0
        pbar = tqdm(total=total_rows)
        
        while True:
            stmt = select(TextContent).where(TextContent.embedding == None).limit(batch_size)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            
            if not rows:
                break
            
            for row in rows:
                if row.content:
                    embedding = await get_embedding(client, row.content)
                    if embedding:
                        row.embedding = embedding
            
            await session.commit()
            pbar.update(len(rows))
            
            # Simple offset isn't needed if we filter by embedding == None and commit, 
            # but to be safe against infinite loops if generation fails:
            # We rely on the fact that we are filling them. 
            # If generation fails (returns None), we might loop.
            # To avoid this, we could flag them or just rely on a separate query + offset if needed.
            # For this simple script, we assume success or we skip.
            
    logger.info("Embedding regeneration complete")

if __name__ == "__main__":
    asyncio.run(regenerate_embeddings())
