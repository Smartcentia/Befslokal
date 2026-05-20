"""
Admin API Usage Statistics Endpoints

Provides endpoints for viewing OpenAI API usage and costs.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.api.deps import get_db, get_current_active_superuser
from app.domains.core.models.api_usage import APIUsage
from app.services.api_usage_tracker import get_usage_stats

# Protect router with admin check
router = APIRouter(
    prefix="/api-usage",
    dependencies=[Depends(get_current_active_superuser)]
)


@router.get("/summary")
async def get_usage_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get OpenAI API usage summary for the specified period.

    Returns:
        - Total requests, tokens, and cost
        - Breakdown by model
        - Breakdown by endpoint
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    stats = await get_usage_stats(
        db=db,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "summary": {
            "total_requests": stats["total_requests"],
            "total_tokens": stats["total_tokens"],
            "total_cost_usd": stats["total_cost"],
            "by_model": stats["by_model"],
            "by_endpoint": stats["by_endpoint"]
        }
    }


@router.get("/by-model/{model_name}")
async def get_usage_by_model(
    model_name: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for a specific model.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    stats = await get_usage_stats(
        db=db,
        start_date=start_date,
        end_date=end_date,
        model=model_name
    )

    return {
        "model": model_name,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "stats": stats
    }


@router.get("/recent")
async def get_recent_usage(
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent API usage records.
    """
    result = await db.execute(
        select(APIUsage)
        .order_by(APIUsage.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    return {
        "records": [
            {
                "id": str(record.id),
                "endpoint": record.endpoint,
                "model": record.model,
                "prompt_tokens": record.prompt_tokens,
                "completion_tokens": record.completion_tokens,
                "total_tokens": record.total_tokens,
                "estimated_cost": record.estimated_cost,
                "user_id": record.user_id,
                "created_at": record.created_at.isoformat()
            }
            for record in records
        ]
    }


@router.get("/daily-stats")
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily aggregated statistics.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query daily aggregates
    from sqlalchemy import cast, Date

    result = await db.execute(
        select(
            cast(APIUsage.created_at, Date).label('date'),
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.estimated_cost).label('cost')
        )
        .where(APIUsage.created_at >= start_date)
        .where(APIUsage.created_at <= end_date)
        .group_by(cast(APIUsage.created_at, Date))
        .order_by(cast(APIUsage.created_at, Date).desc())
    )

    rows = result.all()

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "daily_stats": [
            {
                "date": row.date.isoformat(),
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost_usd": float(row.cost or 0)
            }
            for row in rows
        ]
    }
