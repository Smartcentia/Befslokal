from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent_memory import AgentMemory
from app.services.embeddings import generate_query_embedding
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

class ToolDiscoveryService:
    @staticmethod
    async def find_relevant_tools(
        db: AsyncSession,
        user_query: str,
        limit: int = 3,
        min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Search for tools in memory based on user intent."""
        try:
            query_embedding = generate_query_embedding(user_query)
            
            # cosine_distance is 1 - similarity
            # Since we only want tools, we filter by metadata type
            from sqlalchemy import cast, String
            stmt = (
                select(AgentMemory)
                .where(cast(AgentMemory.additional_metadata['type'], String) == '"tool_definition"') # JSONB strings are quoted in cast
                .order_by(AgentMemory.embedding.cosine_distance(query_embedding))
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            discovered_tools = []
            for m in memories:
                # We could calculate similarity here for filtering, but for now we trust the top results
                discovered_tools.append({
                    "name": m.additional_metadata.get("tool_name"),
                    "description": m.content,
                    "parameters": m.additional_metadata.get("parameters", {}),
                    "id": str(m.id)
                })
                
            logger.info(f"Toolbox search for '{user_query}' discovered {len(discovered_tools)} tools")
            return discovered_tools
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            return []
