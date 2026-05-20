"""
Query Library Service - Manages reusable query patterns

This service:
1. Finds similar queries from library using full-text search
2. Saves successful query patterns from query_logs
3. Tracks usage and success rates
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, List
from app.services.infrastructure.logger import get_logger
import re

logger = get_logger(__name__)


class QueryLibraryService:
    """
    Manages a library of proven SQL query patterns.
    Learns from successful queries and suggests reuse.
    """

    async def find_similar_query(
        self,
        db: AsyncSession,
        user_question: str,
        min_usage_count: int = 3,
        min_success_rate: float = 0.90
    ) -> Optional[Dict]:
        """
        Find a similar query pattern in library using full-text search.

        Args:
            db: Database session
            user_question: The user's current question
            min_usage_count: Minimum times query must have been used
            min_success_rate: Minimum success rate (0.0-1.0)

        Returns:
            Query pattern dict or None
        """
        try:
            # Use PostgreSQL full-text search with ts_rank for relevance scoring
            result = await db.execute(text("""
                SELECT
                    query_id,
                    query_name,
                    sql_template,
                    description,
                    usage_count,
                    success_rate,
                    avg_execution_time_ms,
                    ts_rank(
                        to_tsvector('norwegian', user_question_pattern),
                        plainto_tsquery('norwegian', :question)
                    ) as relevance_score
                FROM query_library
                WHERE
                    to_tsvector('norwegian', user_question_pattern) @@
                    plainto_tsquery('norwegian', :question)
                    AND usage_count >= :min_usage
                    AND success_rate >= :min_success
                ORDER BY relevance_score DESC, usage_count DESC
                LIMIT 1
            """), {
                "question": user_question,
                "min_usage": min_usage_count,
                "min_success": min_success_rate
            })

            row = result.fetchone()
            if row:
                logger.info(f"Found similar query: {row.query_name} (relevance: {row.relevance_score:.3f}, usage: {row.usage_count})")
                return {
                    "query_id": str(row.query_id),
                    "query_name": row.query_name,
                    "sql_template": row.sql_template,
                    "description": row.description,
                    "usage_count": row.usage_count,
                    "success_rate": row.success_rate,
                    "avg_execution_time_ms": row.avg_execution_time_ms
                }

            logger.debug(f"No similar query found for: {user_question[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Error finding similar query: {e}")
            return None

    async def save_query_pattern(
        self,
        db: AsyncSession,
        user_question: str,
        sql: str,
        executions: int,
        successes: int,
        avg_time_ms: int
    ) -> bool:
        """
        Save a new reusable query pattern if it meets criteria.

        Criteria:
        - Query executed successfully 3+ times
        - Success rate > 90%
        - Execution time < 5 seconds
        - Not already in library

        Returns:
            True if saved, False otherwise
        """
        try:
            # Check criteria
            if executions < 3:
                logger.debug(f"Query executed only {executions} times, need 3+")
                return False

            success_rate = successes / executions
            if success_rate < 0.90:
                logger.debug(f"Query success rate {success_rate:.2f} < 0.90")
                return False

            if avg_time_ms > 5000:
                logger.debug(f"Query avg time {avg_time_ms}ms > 5000ms")
                return False

            # Generate query name from SQL
            query_name = self._generate_query_name(sql)

            # Check if already exists
            existing = await db.execute(text("""
                SELECT query_id FROM query_library WHERE query_name = :name
            """), {"name": query_name})

            if existing.fetchone():
                logger.debug(f"Query pattern {query_name} already exists")
                return False

            # Insert new pattern
            await db.execute(text("""
                INSERT INTO query_library
                (query_name, user_question_pattern, sql_template, description,
                 usage_count, success_rate, avg_execution_time_ms, created_by)
                VALUES (:name, :question, :sql, :desc, :count, :rate, :time, 'auto')
            """), {
                "name": query_name,
                "question": user_question,
                "sql": sql,
                "desc": f"Auto-generated from {executions} successful executions (success rate: {success_rate:.1%})",
                "count": executions,
                "rate": success_rate,
                "time": avg_time_ms
            })
            await db.commit()

            logger.info(f"✅ Saved new query pattern: {query_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving query pattern: {e}")
            await db.rollback()
            return False

    async def increment_usage(
        self,
        db: AsyncSession,
        query_id: str,
        success: bool,
        execution_time_ms: int
    ):
        """
        Track query usage and update success rate and avg execution time.

        Args:
            query_id: UUID of the query in library
            success: Whether this execution was successful
            execution_time_ms: Execution time in milliseconds
        """
        try:
            # Recalculate moving averages
            await db.execute(text("""
                UPDATE query_library
                SET
                    usage_count = usage_count + 1,
                    success_rate = (
                        (success_rate * usage_count + :success_value) / (usage_count + 1)
                    ),
                    avg_execution_time_ms = (
                        CASE
                            WHEN avg_execution_time_ms IS NOT NULL
                            THEN ((avg_execution_time_ms * usage_count + :exec_time) / (usage_count + 1))
                            ELSE :exec_time
                        END
                    )::integer,
                    updated_at = NOW()
                WHERE query_id = :id
            """), {
                "id": query_id,
                "success_value": 1.0 if success else 0.0,
                "exec_time": execution_time_ms
            })
            await db.commit()

            logger.debug(f"Updated usage stats for query {query_id}")

        except Exception as e:
            logger.error(f"Error updating query usage: {e}")
            await db.rollback()

    def _generate_query_name(self, sql: str) -> str:
        """
        Generate a descriptive name from SQL query.

        Examples:
        - SELECT ... FROM contracts ORDER BY ... DESC → "top_contracts_desc"
        - SELECT AVG(...) FROM properties GROUP BY region → "avg_properties_by_region"
        """
        sql_lower = sql.lower()

        # Extract table names
        tables = re.findall(r'from\s+(\w+)', sql_lower)
        table = tables[0] if tables else "unknown"

        # Detect operation type
        if "avg(" in sql_lower:
            operation = "avg"
        elif "sum(" in sql_lower:
            operation = "sum"
        elif "count(" in sql_lower:
            operation = "count"
        elif "max(" in sql_lower:
            operation = "max"
        elif "min(" in sql_lower:
            operation = "min"
        else:
            operation = "list"

        # Detect grouping
        if "group by" in sql_lower:
            group_by = re.findall(r'group by\s+[\w.]+\.?(\w+)', sql_lower)
            if group_by:
                operation += f"_by_{group_by[0]}"

        # Detect ordering
        order = ""
        if "order by" in sql_lower:
            if "desc" in sql_lower:
                order = "_desc"
            else:
                order = "_asc"

        # Combine parts
        name = f"{operation}_{table}{order}".strip("_")

        # Ensure uniqueness by adding hash if needed
        import hashlib
        sql_hash = hashlib.md5(sql.encode()).hexdigest()[:6]

        return f"{name}_{sql_hash}"

    async def get_library_stats(self, db: AsyncSession) -> Dict:
        """Get statistics about the query library."""
        try:
            result = await db.execute(text("""
                SELECT
                    COUNT(*) as total_patterns,
                    SUM(usage_count) as total_uses,
                    AVG(usage_count) as avg_uses_per_pattern,
                    AVG(success_rate) as avg_success_rate,
                    AVG(avg_execution_time_ms) as avg_exec_time
                FROM query_library
            """))

            row = result.fetchone()
            if row:
                return {
                    "total_patterns": row.total_patterns,
                    "total_uses": row.total_uses or 0,
                    "avg_uses_per_pattern": float(row.avg_uses_per_pattern or 0),
                    "avg_success_rate": float(row.avg_success_rate or 0),
                    "avg_exec_time_ms": int(row.avg_exec_time or 0)
                }

            return {
                "total_patterns": 0,
                "total_uses": 0,
                "avg_uses_per_pattern": 0.0,
                "avg_success_rate": 0.0,
                "avg_exec_time_ms": 0
            }

        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            return {}

    async def get_most_used_patterns(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict]:
        """Get the most frequently used query patterns."""
        try:
            result = await db.execute(text("""
                SELECT
                    query_name,
                    user_question_pattern,
                    usage_count,
                    success_rate,
                    avg_execution_time_ms,
                    created_at
                FROM query_library
                ORDER BY usage_count DESC
                LIMIT :limit
            """), {"limit": limit})

            return [
                {
                    "query_name": row.query_name,
                    "user_question_pattern": row.user_question_pattern,
                    "usage_count": row.usage_count,
                    "success_rate": float(row.success_rate),
                    "avg_execution_time_ms": row.avg_execution_time_ms,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
                for row in result.fetchall()
            ]

        except Exception as e:
            logger.error(f"Error getting most used patterns: {e}")
            return []

    async def insert_manual_query(
        self,
        db: AsyncSession,
        query_name: str,
        user_question_pattern: str,
        sql_template: str,
        description: str = ""
    ) -> bool:
        """
        Insert a manually curated query pattern (for seeding).
        Uses usage_count=5 and success_rate=1.0 so find_similar_query finds it.
        """
        try:
            existing = await db.execute(text(
                "SELECT query_id FROM query_library WHERE query_name = :name"
            ), {"name": query_name})
            if existing.fetchone():
                logger.info(f"Query {query_name} already exists, skipping")
                return False
            await db.execute(text("""
                INSERT INTO query_library
                (query_name, user_question_pattern, sql_template, description,
                 usage_count, success_rate, created_by)
                VALUES (:name, :question, :sql, :desc, 5, 1.0, 'manual')
            """), {
                "name": query_name,
                "question": user_question_pattern,
                "sql": sql_template,
                "desc": description or f"Manuelt lagt til: {query_name}"
            })
            await db.commit()
            logger.info("✅ Inserted manual query: %s", query_name)
            return True
        except Exception as e:
            logger.error("Failed to insert manual query: %s", e)
            await db.rollback()
            return False


# Singleton instance
query_library_service = QueryLibraryService()
