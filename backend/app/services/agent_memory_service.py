from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent_memory import AgentMemory
from app.services.embeddings import generate_embeddings, generate_query_embedding
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

class AgentMemoryService:
    @staticmethod
    async def add_memory(
        db: AsyncSession,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMemory:
        """Add a new piece of information to agent memory."""
        try:
            embedding = generate_query_embedding(content)
            
            memory = AgentMemory(
                content=content,
                additional_metadata=metadata or {},
                embedding=embedding
            )
            
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            logger.info(f"Added memory: {content[:50]}...")
            return memory
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to add memory: {e}")
            raise

    @staticmethod
    async def search_memory(
        db: AsyncSession,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search agent memory using semantic similarity."""
        try:
            query_embedding = generate_query_embedding(query)
            
            # cosine_distance is 1 - similarity, so we want distance < (1 - min_similarity)
            distance_limit = 1.0 - min_similarity
            
            # Order by distance (closest first)
            from sqlalchemy import cast, String, literal
            
            # Build query with distance calculation for filtering
            distance_expr = AgentMemory.embedding.cosine_distance(query_embedding)
            
            stmt = (
                select(AgentMemory, distance_expr.label('distance'))
            )
            
            # Apply metadata filters if provided
            if filters:
                for key, value in filters.items():
                    # Use ->> operator (astext) for string comparison
                    stmt = stmt.where(AgentMemory.additional_metadata[key].astext == str(value))

            # Filter by similarity threshold and order by distance
            stmt = stmt.where(distance_expr < distance_limit)
            stmt = stmt.order_by(distance_expr).limit(limit)
            
            result = await db.execute(stmt)
            rows = result.all()
            
            # Format results with similarity score
            formatted_results = []
            for row in rows:
                m = row[0]  # AgentMemory object
                distance = row[1]  # distance value
                similarity = 1.0 - distance  # Convert distance to similarity
                
                formatted_results.append({
                    "id": str(m.id),
                    "content": m.content,
                    "metadata": m.additional_metadata,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "similarity": round(similarity, 3)
                })
            
            logger.info(f"Search for '{query}' returned {len(formatted_results)} results (min_similarity={min_similarity})")
            return formatted_results
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    @staticmethod
    async def clear_memory(db: AsyncSession):
        """Clear all agent memory (Warning: Destructive)."""
        try:
            from sqlalchemy import delete
            await db.execute(delete(AgentMemory))
            await db.commit()
            logger.warning("Agent memory cleared!")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to clear memory: {e}")
            raise
