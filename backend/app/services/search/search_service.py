"""
Full-text search service using PostgreSQL native search capabilities.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.text_content import TextContent
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)


async def search_fulltext(
    session: AsyncSession,
    query: str,
    limit: int = 10,
    offset: int = 0,
    language: str = 'norwegian'
) -> List[Dict[str, Any]]:
    """
    Perform full-text search on text_content using PostgreSQL.
    
    Args:
        session: Database session
        query: Search query string
        limit: Maximum number of results
        offset: Offset for pagination
        language: Language for text search (default: norwegian)
    
    Returns:
        List of search results with metadata and ranking
    """
    
    try:
        # Build PostgreSQL tsquery
        # Use plainto_tsquery for simple queries (handles special chars automatically)
        search_query = text(f"""
            SELECT 
                text_id,
                source_index_id,
                content,
                source_file,
                source_type,
                category,
                chunk_index,
                additional_metadata,
                contract_id,
                property_id,
                unit_id,
                created_at,
                ts_rank(search_vector, plainto_tsquery(:language, :query)) as rank,
                ts_headline(
                    :language,
                    content,
                    plainto_tsquery(:language, :query),
                    'MaxWords=50, MinWords=25, ShortWord=3, HighlightAll=FALSE, MaxFragments=1'
                ) as headline
            FROM text_content
            WHERE 
                search_vector @@ plainto_tsquery(:language, :query)
                OR content ILIKE '%' || :query || '%'
            ORDER BY rank DESC, created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = await session.execute(
            search_query,
            {
                'query': query,
                'language': language,
                'limit': limit,
                'offset': offset
            }
        )
        
        rows = result.fetchall()
        
        # Format results
        results = []
        for row in rows:
            results.append({
                'text_id': str(row.text_id),
                'source_index_id': row.source_index_id,
                'content': row.content,
                'source_file': row.source_file,
                'source_type': row.source_type,
                'category': row.category,
                'chunk_index': row.chunk_index,
                'metadata': row.additional_metadata,
                'contract_id': str(row.contract_id) if row.contract_id else None,
                'property_id': str(row.property_id) if row.property_id else None,
                'unit_id': str(row.unit_id) if row.unit_id else None,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'rank': float(row.rank),
                'headline': row.headline  # Highlighted snippet
            })
        
        logger.info(f"Full-text search for '{query}' returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error in full-text search: {e}")
        raise


async def get_search_stats(session: AsyncSession) -> Dict[str, Any]:
    """Get statistics about searchable content."""
    
    try:
        # Count total documents
        total_result = await session.execute(
            select(func.count(TextContent.text_id))
        )
        total_count = total_result.scalar()
        
        # Count documents with search vectors
        indexed_result = await session.execute(
            select(func.count(TextContent.text_id)).where(
                TextContent.search_vector.isnot(None)
            )
        )
        indexed_count = indexed_result.scalar()
        
        # Count by category
        category_result = await session.execute(
            select(
                TextContent.category,
                func.count(TextContent.text_id)
            ).group_by(TextContent.category)
        )
        categories = {row[0] or 'uncategorized': row[1] for row in category_result}
        
        return {
            'total_documents': total_count,
            'indexed_documents': indexed_count,
            'categories': categories
        }
        
    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        raise


async def search_hybrid(
    session: AsyncSession,
    query: str,
    embedding: List[float],
    limit: int = 10,
    language: str = 'norwegian'
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (Vector + Full-text) using RRF for ranking.
    """
    try:
        # 1. Vector Search (Semantic)
        # Using cosine distance (<=>). Lower is better. 
        # We convert to similarity/score for RRF.
        # 1. Prepare Queries
        
        # Vector Search Query
        vector_stmt = text(f"""
            SELECT 
                text_id,
                content,
                source_file,
                source_type,
                category,
                additional_metadata,
                contract_id,
                property_id,
                created_at,
                1 - (embedding <=> :embedding) as vector_score
            FROM text_content
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding ASC
            LIMIT :limit
        """)

        # Keyword Search Query
        keyword_stmt = text(f"""
            SELECT 
                text_id,
                content,
                source_file,
                source_type,
                category,
                additional_metadata,
                contract_id,
                property_id,
                created_at,
                ts_rank(search_vector, plainto_tsquery(:language, :query)) as text_rank
            FROM text_content
            WHERE 
                search_vector @@ plainto_tsquery(:language, :query)
            ORDER BY text_rank DESC
            LIMIT :limit
        """)

        # 2. Execute Sequentially (AsyncSession does not support concurrent execution)
        vector_result = await session.execute(vector_stmt, {'embedding': str(embedding), 'limit': limit * 2})
        keyword_result = await session.execute(keyword_stmt, {'query': query, 'language': language, 'limit': limit * 2})
        
        vector_rows = vector_result.fetchall()
        keyword_rows = keyword_result.fetchall()

        # 3. Reciprocal Rank Fusion (RRF)
        # score = 1 / (k + rank)
        k = 60
        scores: Dict[str, float] = {}
        docs: Dict[str, Any] = {}

        # Process Vector Results
        for rank, row in enumerate(vector_rows):
            doc_id = str(row.text_id)
            scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank + 1))
            docs[doc_id] = row

        # Process Keyword Results
        for rank, row in enumerate(keyword_rows):
            doc_id = str(row.text_id)
            if doc_id not in docs:
                docs[doc_id] = row
            scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank + 1))

        # Sort by accumulated score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:limit]

        results = []
        for doc_id in sorted_ids:
            row = docs[doc_id]
            # Construct result dict (handling potential missing fields if row structure differs slightly?)
            # Both queries return compatible columns.
            results.append({
                'text_id': doc_id,
                'content': row.content,
                'source_file': row.source_file,
                'source_type': row.source_type,
                'category': row.category,
                'metadata': row.additional_metadata,
                'contract_id': str(row.contract_id) if row.contract_id else None,
                'property_id': str(row.property_id) if row.property_id else None,
                'score': scores[doc_id],
                # 'vector_score': getattr(row, 'vector_score', None),
                # 'text_rank': getattr(row, 'text_rank', None)
            })

        logger.info(f"Hybrid search for '{query}' returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        # Fallback to simple full-text if vector fails (e.g. pgvector issue)
        logger.info("Falling back to standard full-text search")
        return await search_fulltext(session, query, limit, 0, language)
