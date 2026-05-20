"""
Query Logging Service - Centralized logging for all SQL query executions.

This service captures every query attempt (success and failure) with comprehensive
metadata to enable the self-learning loop.
"""

from uuid import UUID
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import json

logger = logging.getLogger(__name__)


class QueryLoggingService:
    """Centralized service for logging all SQL query executions"""

    @staticmethod
    async def log_query_execution(
        db: AsyncSession,
        user_question: str,
        generated_sql: Optional[str],
        execution_success: bool,
        result_count: int,
        execution_time_ms: int,
        error_message: Optional[str],
        confidence_score: float,
        model_used: str,
        cache_hit: bool,
        context_data: Dict,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        retry_count: int = 0,
        parent_log_id: Optional[UUID] = None
    ) -> Optional[UUID]:
        """
        Log query execution to database.

        Args:
            db: Database session
            user_question: Original user question
            generated_sql: Generated SQL query (if any)
            execution_success: Whether execution succeeded
            result_count: Number of results returned
            execution_time_ms: Execution time in milliseconds
            error_message: Error message if failed
            confidence_score: Confidence score (0.0-1.0)
            model_used: Model used for generation (gpt-4o, gpt-4o-mini, query_library)
            cache_hit: Whether result was from cache
            context_data: Additional context (query_type, source, etc.)
            user_id: User ID (if available)
            conversation_id: Conversation ID (if available)
            retry_count: Number of retries (0 for first attempt)
            parent_log_id: Parent log ID for retries

        Returns:
            log_id if successful, None if logging failed
        """
        try:
            result = await db.execute(text("""
                INSERT INTO query_logs (
                    user_question, generated_sql, query_type, execution_success,
                    result_count, execution_time_ms, error_message, context_data,
                    user_id, conversation_id, confidence_score, model_used,
                    cache_hit, retry_count, parent_log_id
                )
                VALUES (
                    :question, :sql, :query_type, :success,
                    :count, :time_ms, :error, CAST(:context AS jsonb),
                    :user_id, :conv_id, :confidence, :model,
                    :cache_hit, :retry, :parent
                )
                RETURNING log_id
            """), {
                "question": user_question[:1000] if user_question else None,
                "sql": generated_sql[:5000] if generated_sql else None,
                "query_type": context_data.get("query_type", "unknown"),
                "success": execution_success,
                "count": result_count,
                "time_ms": execution_time_ms,
                "error": error_message[:500] if error_message else None,
                "context": json.dumps(context_data),
                "user_id": user_id,
                "conv_id": conversation_id,
                "confidence": confidence_score,
                "model": model_used,
                "cache_hit": cache_hit,
                "retry": retry_count,
                "parent": parent_log_id
            })

            await db.commit()
            log_id = result.scalar_one()

            # Log success at debug level (don't spam logs)
            logger.debug(
                f"Query logged: {log_id} | "
                f"success={execution_success} | "
                f"confidence={confidence_score:.2f} | "
                f"model={model_used} | "
                f"time={execution_time_ms}ms"
            )

            return log_id

        except Exception as e:
            logger.error(f"Failed to log query execution: {e}", exc_info=True)
            await db.rollback()
            # Don't fail the main query if logging fails
            return None

    @staticmethod
    async def get_recent_logs(
        db: AsyncSession,
        limit: int = 100,
        success_only: bool = False
    ) -> list:
        """
        Get recent query logs for analysis.

        Args:
            db: Database session
            limit: Maximum number of logs to return
            success_only: If True, only return successful queries

        Returns:
            List of query log dictionaries
        """
        try:
            query = """
                SELECT
                    log_id,
                    user_question,
                    generated_sql,
                    execution_success,
                    result_count,
                    execution_time_ms,
                    confidence_score,
                    model_used,
                    cache_hit,
                    retry_count,
                    timestamp
                FROM query_logs
                WHERE 1=1
            """

            if success_only:
                query += " AND execution_success = true"

            query += " ORDER BY timestamp DESC LIMIT :limit"

            result = await db.execute(text(query), {"limit": limit})

            logs = []
            for row in result.fetchall():
                logs.append({
                    "log_id": str(row.log_id),
                    "user_question": row.user_question,
                    "generated_sql": row.generated_sql,
                    "execution_success": row.execution_success,
                    "result_count": row.result_count,
                    "execution_time_ms": row.execution_time_ms,
                    "confidence_score": row.confidence_score,
                    "model_used": row.model_used,
                    "cache_hit": row.cache_hit,
                    "retry_count": row.retry_count,
                    "timestamp": row.timestamp.isoformat()
                })

            return logs

        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_stats(db: AsyncSession, days: int = 7) -> Dict:
        """
        Get query logging statistics.

        Args:
            db: Database session
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        try:
            # Simple approach: just get all recent logs without time filter for now
            result = await db.execute(text("""
                SELECT
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN execution_success THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN NOT execution_success THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                    SUM(CASE WHEN retry_count > 0 THEN 1 ELSE 0 END) as retries,
                    AVG(confidence_score) as avg_confidence,
                    AVG(execution_time_ms) as avg_execution_time,
                    COUNT(DISTINCT model_used) as models_used
                FROM query_logs
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
            """))

            row = result.fetchone()

            if row and row.total_queries > 0:
                return {
                    "total_queries": row.total_queries,
                    "successful": row.successful,
                    "failed": row.failed,
                    "success_rate": round(row.successful / row.total_queries, 3),
                    "cache_hits": row.cache_hits,
                    "cache_hit_rate": round(row.cache_hits / row.total_queries, 3),
                    "retries": row.retries,
                    "retry_rate": round(row.retries / row.total_queries, 3),
                    "avg_confidence": round(row.avg_confidence or 0.0, 3),
                    "avg_execution_time_ms": round(row.avg_execution_time or 0.0, 0),
                    "models_used": row.models_used
                }
            else:
                return {
                    "total_queries": 0,
                    "successful": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                    "cache_hits": 0,
                    "cache_hit_rate": 0.0,
                    "retries": 0,
                    "retry_rate": 0.0,
                    "avg_confidence": 0.0,
                    "avg_execution_time_ms": 0.0,
                    "models_used": 0
                }

        except Exception as e:
            logger.error(f"Failed to get query stats: {e}", exc_info=True)
            return {}
