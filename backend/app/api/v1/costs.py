"""
Cost Monitoring API Router

Provides endpoints for infrastructure cost tracking and analysis.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import subprocess
import json
import sys
from pathlib import Path

from app.api.deps import get_db

router = APIRouter()


# Pydantic models for API responses
class CostDataPoint(BaseModel):
    """Single cost data point."""
    id: int
    service_name: str
    collection_date: datetime
    estimated_cost_usd: Optional[float]
    active_time_seconds: Optional[int]
    cpu_used_seconds: Optional[int]
    storage_gb: Optional[float]
    bandwidth_gb: Optional[float]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class CostSummary(BaseModel):
    """Summary of costs across all services."""
    total_cost_usd: float
    period_start: datetime
    period_end: datetime
    services: dict


class ServiceCostBreakdown(BaseModel):
    """Cost breakdown by service."""
    service_name: str
    total_cost_usd: float
    data_points: int
    latest_collection: Optional[datetime]
    average_cost_usd: float


class CostTimeline(BaseModel):
    """Cost timeline data."""
    date: datetime
    total_cost_usd: float
    by_service: dict


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get cost summary for the specified period.
    
    Returns total costs and breakdown by service.
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()
    
    # Query total costs by service
    query = text("""
        SELECT 
            service_name,
            SUM(estimated_cost_usd) as total_cost,
            COUNT(*) as data_points,
            MAX(collection_date) as latest_collection,
            AVG(estimated_cost_usd) as avg_cost
        FROM infrastructure_costs
        WHERE collection_date >= :start_date
            AND collection_date <= :end_date
        GROUP BY service_name
        ORDER BY total_cost DESC
    """)
    
    result = await db.execute(
        query,
        {"start_date": period_start, "end_date": period_end}
    )
    rows = result.fetchall()
    
    services = {}
    total_cost = 0.0
    
    for row in rows:
        service_name = row[0]
        service_total = float(row[1]) if row[1] else 0.0
        total_cost += service_total
        
        services[service_name] = {
            "total_cost_usd": service_total,
            "data_points": row[2],
            "latest_collection": row[3],
            "average_cost_usd": float(row[4]) if row[4] else 0.0
        }
    
    return CostSummary(
        total_cost_usd=total_cost,
        period_start=period_start,
        period_end=period_end,
        services=services
    )


@router.get("/by-service", response_model=List[ServiceCostBreakdown])
async def get_costs_by_service(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get cost breakdown by service."""
    period_start = datetime.utcnow() - timedelta(days=days)
    
    query = text("""
        SELECT 
            service_name,
            SUM(estimated_cost_usd) as total_cost,
            COUNT(*) as data_points,
            MAX(collection_date) as latest_collection,
            AVG(estimated_cost_usd) as avg_cost
        FROM infrastructure_costs
        WHERE collection_date >= :start_date
        GROUP BY service_name
        ORDER BY total_cost DESC
    """)
    
    result = await db.execute(query, {"start_date": period_start})
    rows = result.fetchall()
    
    breakdown = []
    for row in rows:
        breakdown.append(ServiceCostBreakdown(
            service_name=row[0],
            total_cost_usd=float(row[1]) if row[1] else 0.0,
            data_points=row[2],
            latest_collection=row[3],
            average_cost_usd=float(row[4]) if row[4] else 0.0
        ))
    
    return breakdown


@router.get("/timeline", response_model=List[CostTimeline])
async def get_cost_timeline(
    days: int = Query(default=30, ge=1, le=365),
    granularity: str = Query(default="day", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get cost timeline over time.
    
    Shows how costs evolve over the specified period.
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    
    # Determine date grouping based on granularity
    date_trunc = {
        "day": "day",
        "week": "week",
        "month": "month"
    }[granularity]
    
    query = text(f"""
        SELECT 
            DATE_TRUNC(:granularity, collection_date) as period,
            service_name,
            SUM(estimated_cost_usd) as total_cost
        FROM infrastructure_costs
        WHERE collection_date >= :start_date
        GROUP BY period, service_name
        ORDER BY period, service_name
    """)
    
    result = await db.execute(
        query,
        {"start_date": period_start, "granularity": date_trunc}
    )
    rows = result.fetchall()
    
    # Group by period
    timeline_dict = {}
    for row in rows:
        period = row[0]
        service_name = row[1]
        cost = float(row[2]) if row[2] else 0.0
        
        if period not in timeline_dict:
            timeline_dict[period] = {
                "date": period,
                "total_cost_usd": 0.0,
                "by_service": {}
            }
        
        timeline_dict[period]["by_service"][service_name] = cost
        timeline_dict[period]["total_cost_usd"] += cost
    
    # Convert to list
    timeline = [
        CostTimeline(**data)
        for data in sorted(timeline_dict.values(), key=lambda x: x["date"])
    ]
    
    return timeline


@router.get("/latest", response_model=List[CostDataPoint])
async def get_latest_costs(
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent cost data for each service."""
    query = text("""
        WITH ranked_costs AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY service_name ORDER BY collection_date DESC) as rn
            FROM infrastructure_costs
        )
        SELECT 
            id, service_name, collection_date, estimated_cost_usd,
            active_time_seconds, cpu_used_seconds, storage_gb, bandwidth_gb, notes
        FROM ranked_costs
        WHERE rn = 1
        ORDER BY service_name
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    costs = []
    for row in rows:
        costs.append(CostDataPoint(
            id=row[0],
            service_name=row[1],
            collection_date=row[2],
            estimated_cost_usd=float(row[3]) if row[3] else None,
            active_time_seconds=row[4],
            cpu_used_seconds=row[5],
            storage_gb=float(row[6]) if row[6] else None,
            bandwidth_gb=float(row[7]) if row[7] else None,
            notes=row[8]
        ))
    
    return costs


@router.post("/collect")
async def trigger_cost_collection(
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger immediate cost collection.
    
    Runs the cost monitor script and saves results to database.
    """
    try:
        # Get path to cost monitor script
        backend_path = Path(__file__).parent.parent.parent.parent
        script_path = backend_path / "scripts" / "cost_monitor.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Cost monitor script not found at {script_path}"
            )
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Cost collection failed: {result.stderr}"
            )
        
        # Parse result
        data = json.loads(result.stdout)
        
        return {
            "status": "success",
            "message": "Cost data collected successfully",
            "data": data
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Cost collection timed out"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse cost data: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/export")
async def export_costs(
    days: int = Query(default=30, ge=1, le=365),
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export cost data in CSV or JSON format.
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    
    query = text("""
        SELECT 
            id, service_name, collection_date, estimated_cost_usd,
            active_time_seconds, cpu_used_seconds, storage_gb, 
            bandwidth_gb, notes, created_at
        FROM infrastructure_costs
        WHERE collection_date >= :start_date
        ORDER BY collection_date DESC, service_name
    """)
    
    result = await db.execute(query, {"start_date": period_start})
    rows = result.fetchall()
    
    if format == "json":
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "service_name": row[1],
                "collection_date": row[2].isoformat() if row[2] else None,
                "estimated_cost_usd": float(row[3]) if row[3] else None,
                "active_time_seconds": row[4],
                "cpu_used_seconds": row[5],
                "storage_gb": float(row[6]) if row[6] else None,
                "bandwidth_gb": float(row[7]) if row[7] else None,
                "notes": row[8],
                "created_at": row[9].isoformat() if row[9] else None
            })
        
        return {"format": "json", "data": data}
    
    else:  # CSV
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID", "Service", "Collection Date", "Cost (USD)",
            "Active Time (s)", "CPU Used (s)", "Storage (GB)",
            "Bandwidth (GB)", "Notes", "Created At"
        ])
        
        # Write data
        for row in rows:
            writer.writerow([
                row[0],
                row[1],
                row[2].isoformat() if row[2] else "",
                f"{row[3]:.2f}" if row[3] else "",
                row[4] or "",
                row[5] or "",
                f"{row[6]:.2f}" if row[6] else "",
                f"{row[7]:.2f}" if row[7] else "",
                row[8] or "",
                row[9].isoformat() if row[9] else ""
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=infrastructure_costs_{days}days.csv"
            }
        )
