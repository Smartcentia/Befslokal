
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
import logging
from app.services.embeddings import generate_query_embedding

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    @staticmethod
    async def add_entity(
        db: AsyncSession,
        name: str,
        label: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """Add a node (entity) to the knowledge graph."""
        try:
            entity_id = uuid.uuid4()
            embedding = generate_query_embedding(f"{label}: {name}. {description or ''}")
            
            await db.execute(
                text("""
                    INSERT INTO graph_entities (id, name, label, description, metadata, embedding)
                    VALUES (:id, :name, :label, :description, :metadata, :embedding)
                """),
                {
                    "id": entity_id,
                    "name": name,
                    "label": label.upper(),
                    "description": description,
                    "metadata": metadata or {},
                    "embedding": embedding
                }
            )
            await db.commit()
            return entity_id
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to add entity: {e}")
            raise

    @staticmethod
    async def add_relationship(
        db: AsyncSession,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relation_type: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add an edge (relationship) between two entities."""
        try:
            await db.execute(
                text("""
                    INSERT INTO graph_relationships (id, source_id, target_id, relation_type, description, metadata)
                    VALUES (:id, :source_id, :target_id, :relation_type, :description, :metadata)
                """),
                {
                    "id": uuid.uuid4(),
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": relation_type.upper(),
                    "description": description,
                    "metadata": metadata or {}
                }
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to add relationship: {e}")
            raise

    @staticmethod
    async def search_entities(db: AsyncSession, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for entities using semantic similarity."""
        try:
            query_embedding = generate_query_embedding(query)
            
            # Using pgvector similarity
            result = await db.execute(
                text("""
                    SELECT id, name, label, description, metadata, 
                           1 - (embedding <=> :embedding) as similarity
                    FROM graph_entities
                    WHERE 1 - (embedding <=> :embedding) > 0.6
                    ORDER BY embedding <=> :embedding
                    LIMIT :limit
                """),
                {"embedding": query_embedding, "limit": limit}
            )
            
            rows = result.fetchall()
            return [dict(r._mapping) for r in rows]
        except Exception as e:
            logger.error(f"Entity search failed: {e}")
            return []

    @staticmethod
    async def get_relationships(db: AsyncSession, entity_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all relationships for a given entity (incoming and outgoing)."""
        try:
            result = await db.execute(
                text("""
                    SELECT r.relation_type, r.description as rel_desc,
                           e_source.name as source_name, e_source.label as source_label,
                           e_target.name as target_name, e_target.label as target_label
                    FROM graph_relationships r
                    JOIN graph_entities e_source ON r.source_id = e_source.id
                    JOIN graph_entities e_target ON r.target_id = e_target.id
                    WHERE r.source_id = :eid OR r.target_id = :eid
                """),
                {"eid": entity_id}
            )
            
            rows = result.fetchall()
            return [dict(r._mapping) for r in rows]
        except Exception as e:
            logger.error(f"Relationship retrieval failed: {e}")
            return []
