"""
Scheduled task to analyze query_logs and save successful patterns to query_library.

Run this daily via cron or scheduled job:
0 2 * * * cd /app && python3 app/tasks/save_query_patterns.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal
from app.services.query_library_service import query_library_service
from app.services.infrastructure.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


async def save_successful_patterns():
    """
    Analyze yesterday's queries and save successful patterns to query_library.

    Criteria:
    - Query executed 3+ times in last 7 days
    - Success rate > 90%
    - Average execution time < 5 seconds
    """
    logger.info("=== Starting Query Pattern Analysis ===")

    async with SessionLocal() as db:
        try:
            # Find frequently used queries from last 7 days
            result = await db.execute(text("""
                SELECT
                    user_question,
                    generated_sql,
                    COUNT(*) as executions,
                    SUM(CASE WHEN execution_success THEN 1 ELSE 0 END) as successes,
                    AVG(execution_time_ms) as avg_time
                FROM query_logs
                WHERE
                    timestamp > NOW() - INTERVAL '7 days'
                    AND execution_success = true
                    AND generated_sql IS NOT NULL
                    AND user_question IS NOT NULL
                GROUP BY user_question, generated_sql
                HAVING COUNT(*) >= 3
                ORDER BY COUNT(*) DESC
            """))

            patterns_saved = 0
            patterns_skipped = 0

            for row in result.fetchall():
                success_rate = row.successes / row.executions

                logger.info(f"\nAnalyzing pattern:")
                logger.info(f"  Question: {row.user_question[:60]}...")
                logger.info(f"  Executions: {row.executions}, Success rate: {success_rate:.1%}, Avg time: {row.avg_time:.0f}ms")

                saved = await query_library_service.save_query_pattern(
                    db,
                    user_question=row.user_question,
                    sql=row.generated_sql,
                    executions=row.executions,
                    successes=row.successes,
                    avg_time_ms=int(row.avg_time)
                )

                if saved:
                    patterns_saved += 1
                else:
                    patterns_skipped += 1

            logger.info(f"\n=== Query Pattern Analysis Complete ===")
            logger.info(f"Patterns saved: {patterns_saved}")
            logger.info(f"Patterns skipped: {patterns_skipped}")

            # Get library stats
            stats = await query_library_service.get_library_stats(db)
            logger.info(f"\nCurrent library stats:")
            logger.info(f"  Total patterns: {stats.get('total_patterns', 0)}")
            logger.info(f"  Total uses: {stats.get('total_uses', 0)}")
            logger.info(f"  Avg success rate: {stats.get('avg_success_rate', 0):.1%}")

        except Exception as e:
            logger.error(f"Error in save_successful_patterns: {e}", exc_info=True)
            raise


async def cleanup_old_logs():
    """
    Clean up query logs older than 90 days to prevent database bloat.
    """
    logger.info("=== Cleaning up old query logs ===")

    async with SessionLocal() as db:
        try:
            result = await db.execute(text("""
                DELETE FROM query_logs
                WHERE timestamp < NOW() - INTERVAL '90 days'
                RETURNING log_id
            """))

            deleted_count = len(result.fetchall())
            await db.commit()

            logger.info(f"Deleted {deleted_count} query logs older than 90 days")

        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}", exc_info=True)
            await db.rollback()


async def main():
    """Main entry point for scheduled task."""
    try:
        # Save successful patterns
        await save_successful_patterns()

        # Cleanup old logs
        await cleanup_old_logs()

        logger.info("✅ Task completed successfully")
        return 0

    except Exception as e:
        logger.error(f"❌ Task failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
