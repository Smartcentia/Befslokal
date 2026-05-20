"""
API Usage Tracker

Tracks OpenAI API usage for cost monitoring and analytics.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.core.models.api_usage import APIUsage

logger = logging.getLogger(__name__)


# Pricing per 1M tokens (as of Jan 2025)
# https://openai.com/api/pricing/
PRICING = {
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.150, "completion": 0.600},
    "gpt-4o-2024-11-20": {"prompt": 2.50, "completion": 10.00},
    "gpt-4": {"prompt": 30.00, "completion": 60.00},
    "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
    "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    "text-embedding-3-small": {"prompt": 0.020, "completion": 0.0},
    "text-embedding-3-large": {"prompt": 0.130, "completion": 0.0},
    "text-embedding-ada-002": {"prompt": 0.100, "completion": 0.0},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated cost in USD."""
    pricing = PRICING.get(model, {"prompt": 0.0, "completion": 0.0})

    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]

    return prompt_cost + completion_cost


async def track_usage(
    db: AsyncSession,
    endpoint: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    request_path: Optional[str] = None,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> APIUsage:
    """
    Track API usage in database.

    Args:
        db: Database session
        endpoint: API endpoint name (e.g., "chat", "embeddings")
        model: Model name (e.g., "gpt-4o-mini")
        prompt_tokens: Input tokens used
        completion_tokens: Output tokens used
        request_path: HTTP request path
        user_id: Optional user identifier
        conversation_id: Optional conversation identifier
        error_message: Optional error message if request failed

    Returns:
        APIUsage record
    """
    total_tokens = prompt_tokens + completion_tokens
    estimated_cost = calculate_cost(model, prompt_tokens, completion_tokens)

    usage = APIUsage(
        endpoint=endpoint,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        request_path=request_path,
        user_id=user_id,
        conversation_id=conversation_id,
        error_message=error_message,
        created_at=datetime.utcnow()
    )

    db.add(usage)

    try:
        await db.commit()
        logger.info(f"Tracked usage: {model} - {total_tokens} tokens - ${estimated_cost:.4f}")
    except Exception as e:
        logger.error(f"Failed to track usage: {e}")
        await db.rollback()

    return usage


async def get_usage_stats(
    db: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    model: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get usage statistics.

    Args:
        db: Database session
        start_date: Filter by start date
        end_date: Filter by end date
        model: Filter by model name
        user_id: Filter by user ID

    Returns:
        Dictionary with usage statistics
    """
    query = select(APIUsage)

    if start_date:
        query = query.where(APIUsage.created_at >= start_date)
    if end_date:
        query = query.where(APIUsage.created_at <= end_date)
    if model:
        query = query.where(APIUsage.model == model)
    if user_id:
        query = query.where(APIUsage.user_id == user_id)

    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_model": {},
            "by_endpoint": {}
        }

    total_tokens = sum(r.total_tokens for r in records)
    total_cost = sum(r.estimated_cost for r in records)

    # Group by model
    by_model = {}
    for record in records:
        if record.model not in by_model:
            by_model[record.model] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        by_model[record.model]["requests"] += 1
        by_model[record.model]["tokens"] += record.total_tokens
        by_model[record.model]["cost"] += record.estimated_cost

    # Group by endpoint
    by_endpoint = {}
    for record in records:
        if record.endpoint not in by_endpoint:
            by_endpoint[record.endpoint] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        by_endpoint[record.endpoint]["requests"] += 1
        by_endpoint[record.endpoint]["tokens"] += record.total_tokens
        by_endpoint[record.endpoint]["cost"] += record.estimated_cost

    return {
        "total_requests": len(records),
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
        "by_model": by_model,
        "by_endpoint": by_endpoint
    }
