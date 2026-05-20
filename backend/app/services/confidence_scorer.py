"""
Confidence Scorer - Calculate confidence scores for generated SQL queries.

The confidence score (0.0-1.0) indicates how likely the generated SQL
is to be correct and produce the expected results.
"""

from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculate confidence score (0.0-1.0) for generated SQL queries"""

    @staticmethod
    def calculate_confidence(
        question: str,
        generated_sql: str,
        query_library_match: Optional[Dict],
        cache_hit: bool,
        model_used: str,
        complexity_detected: bool
    ) -> float:
        """
        Calculate confidence based on multiple factors.

        Scoring hierarchy:
        1. Query Library hit (proven pattern) = 0.90-0.98
        2. Cache hit (previously successful) = 0.85-0.90
        3. Freshly generated = 0.65-0.85 (depends on model and complexity)

        Args:
            question: User's question
            generated_sql: Generated SQL query
            query_library_match: Match from query library (if any)
            cache_hit: Whether result was from cache
            model_used: Model used (gpt-4o, gpt-4o-mini, query_library)
            complexity_detected: Whether complexity was detected

        Returns:
            Confidence score between 0.0 and 1.0
        """

        # Priority 1: Query Library hit = highest confidence
        if query_library_match:
            usage_count = query_library_match.get("usage_count", 0)
            success_rate = query_library_match.get("success_rate", 0.0)

            # Proven pattern with high usage and success
            if usage_count >= 10 and success_rate >= 0.95:
                return 0.98
            elif usage_count >= 5 and success_rate >= 0.90:
                return 0.95
            else:
                return 0.90

        # Priority 2: Cache hit = high confidence
        if cache_hit:
            # gpt-4o cached queries have higher confidence
            return 0.90 if model_used == "gpt-4o" else 0.85

        # Priority 3: Freshly generated - base confidence on model
        if model_used == "gpt-4o":
            base_confidence = 0.85
        elif model_used == "gpt-4o-mini":
            base_confidence = 0.75
        elif model_used == "query_library":
            base_confidence = 0.90  # Should have been caught above, but just in case
        else:
            base_confidence = 0.70  # Unknown model

        # Adjust for SQL complexity vs question complexity alignment
        actual_complexity = ConfidenceScorer._detect_sql_complexity(generated_sql)

        # Penalize if complexity detection was wrong
        if complexity_detected != actual_complexity:
            base_confidence -= 0.10
            logger.debug(
                f"Complexity mismatch: detected={complexity_detected}, "
                f"actual={actual_complexity}"
            )

        # Penalize JSONB queries slightly (higher error rate)
        if ConfidenceScorer._has_jsonb_operations(generated_sql):
            base_confidence -= 0.05

        # Ensure confidence is within bounds
        final_confidence = max(0.0, min(1.0, base_confidence))

        logger.debug(
            f"Confidence calculated: {final_confidence:.2f} | "
            f"model={model_used} | "
            f"cache_hit={cache_hit} | "
            f"complexity={actual_complexity}"
        )

        return final_confidence

    @staticmethod
    def _detect_sql_complexity(sql: str) -> bool:
        """
        Detect if SQL query is complex.

        Complex queries include:
        - JSONB operations
        - Aggregations with GROUP BY
        - Window functions
        - Multiple JOINs
        - CTEs (WITH clauses)

        Args:
            sql: SQL query

        Returns:
            True if complex, False if simple
        """
        if not sql:
            return False

        sql_upper = sql.upper()

        # JSONB operations
        has_jsonb = "->>" in sql or "->" in sql

        # Aggregations
        has_aggregation = any(
            kw in sql_upper
            for kw in ["GROUP BY", "AVG(", "SUM(", "COUNT(", "MAX(", "MIN("]
        )

        # Window functions
        has_window = "ROW_NUMBER()" in sql_upper or "PARTITION BY" in sql_upper

        # Multiple JOINs (more than 1)
        join_count = sql_upper.count(" JOIN ")
        has_multiple_joins = join_count > 1

        # CTEs
        has_cte = sql_upper.startswith("WITH ")

        # Complex if any of these are true
        is_complex = (
            has_jsonb or
            has_aggregation or
            has_window or
            has_multiple_joins or
            has_cte
        )

        return is_complex

    @staticmethod
    def _has_jsonb_operations(sql: str) -> bool:
        """
        Check if SQL contains JSONB operations.

        Args:
            sql: SQL query

        Returns:
            True if JSONB operations present
        """
        return "->>" in sql or "->" in sql

    @staticmethod
    def get_confidence_interpretation(confidence: float) -> str:
        """
        Get human-readable interpretation of confidence score.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            Interpretation string
        """
        if confidence >= 0.95:
            return "Very High - Proven pattern"
        elif confidence >= 0.85:
            return "High - Cached or gpt-4o"
        elif confidence >= 0.70:
            return "Medium - Generated with standard patterns"
        elif confidence >= 0.50:
            return "Low - Consider retry with gpt-4o"
        else:
            return "Very Low - Likely to fail"

    @staticmethod
    def should_retry(confidence: float, execution_success: bool) -> bool:
        """
        Determine if query should be retried with gpt-4o.

        Args:
            confidence: Confidence score
            execution_success: Whether execution succeeded

        Returns:
            True if should retry
        """
        # Retry if:
        # - Execution failed AND
        # - Confidence was low (< 0.70)
        return not execution_success and confidence < 0.70
