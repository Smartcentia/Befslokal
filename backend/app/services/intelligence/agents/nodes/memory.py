from langchain_core.messages import SystemMessage
from app.services.intelligence.agents.state import AgentState
from app.services.agent_memory_service import AgentMemoryService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.intelligence.graph_extractor import GraphExtractor
from app.db.session import SessionLocal
from app.services.intelligence.agents.utils import TraceLogger
import logging
import asyncio

logger = logging.getLogger(__name__)

async def memory_node(state: AgentState):
    """
    Node for handling explicit and implicit memory operations.
    1. Saves explicit "Remember X" requests.
    2. Implicitly extracts Knowledge Graph triplets from conversation.
    """
    TraceLogger.log_node("memory", "Oppdaterer hukommelse og kunnskapsgraf...")
    
    messages = state["messages"]
    # Get last user message and assistant answer
    last_user_message = next((m.content for m in reversed(messages) if m.type == "human"), "")
    last_assistant_message = next((m.content for m in reversed(messages) if m.type == "ai"), "")
    
    if not last_user_message:
        return {"next_step": "writer"}

    try:
        async with SessionLocal() as db:
            # 1. Explicit Memory (if relevant)
            if any(key in last_user_message.lower() for key in ["husk", "remember", "noter"]):
                await AgentMemoryService.add_memory(
                    db,
                    last_user_message,
                    metadata={"type": "explicit_memory", "source": "user_request"}
                )
            
            # 2. Implicit Graph Extraction (Hybrid RAG)
            # Combine user message and AI answer to find relationships
            context_to_extract = f"{last_user_message}\n{last_assistant_message}"
            triples = await GraphExtractor.extract_triples(context_to_extract)
            
            if triples:
                logger.info(f"HybridRAG: Extracted {len(triples)} triples from conversation")
                for t in triples:
                    try:
                        source = t.get("source", {})
                        target = t.get("target", {})
                        rel_type = t.get("relation")
                        
                        if not all([source.get("name"), target.get("name"), rel_type]):
                            continue
                            
                        # Generate embeddings using shared service
                        from app.services.embeddings import generate_query_embedding
                        source_emb = generate_query_embedding(f"{source['name']} {source['label']}")
                        target_emb = generate_query_embedding(f"{target['name']} {target['label']}")
                        
                        s_node = await KnowledgeGraphService.upsert_entity(
                            db, source["name"], source["label"], embedding=source_emb
                        )
                        t_node = await KnowledgeGraphService.upsert_entity(
                            db, target["name"], target["label"], embedding=target_emb
                        )
                        
                        await KnowledgeGraphService.add_relationship(
                            db, s_node.id, t_node.id, rel_type
                        )
                    except Exception as trip_err:
                        logger.error(f"Failed to process triple: {trip_err}")

        return {
            "messages": [SystemMessage(content="MEMORY_PROCESSED: Jeg har oppdatert minnet og kunnskapsgrafen min.")],
            "next_step": "writer"
        }
    except Exception as e:
        logger.error(f"Failed to process memory node: {e}")
        return {
            "messages": [SystemMessage(content=f"MEMORY_ERROR: Feil ved oppdatering av minne. {str(e)}")],
            "next_step": "writer"
        }
