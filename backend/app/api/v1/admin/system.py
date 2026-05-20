from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.api.deps import get_db, get_current_active_superuser
from app.domains.core.models.property import Property
from app.services.external.api_clients.kartverket_client import KartverketClient

from scripts.property_enrichment_batch import run_enrichment

# Protect entire router with Admin check
router = APIRouter(dependencies=[Depends(get_current_active_superuser)])


class PropertyEnrichmentRequest(BaseModel):
    apply: bool = False
    confirm_apply: bool = False
    min_score: float = Field(default=0.65, ge=0.0, le=1.0)
    force_description: bool = False
    download_images: bool = True
    limit: Optional[int] = Field(default=None, gt=0)
    report_file: Optional[str] = None


def _enrichment_reports_dir() -> Path:
    return Path("backend") / "data"


def _is_enrichment_report_filename(name: str) -> bool:
    return name.startswith("property_enrichment_report") and name.endswith(".json")


def _safe_report_path(filename: str) -> Path:
    clean = Path(filename).name
    if not _is_enrichment_report_filename(clean):
        raise HTTPException(status_code=400, detail="Invalid report filename")
    return _enrichment_reports_dir() / clean


@router.post("/property-enrichment/batch")
async def run_property_enrichment_batch(
    request: PropertyEnrichmentRequest,
):
    """
    Trigger property enrichment pipeline (dry-run by default).
    Uses Bufdir match file + provider context and returns report summary.
    """
    default_report = (
        Path("backend")
        / "data"
        / f"property_enrichment_report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )

    if request.apply and not request.confirm_apply:
        raise HTTPException(
            status_code=400,
            detail="Apply mode requires confirm_apply=true",
        )

    report_path = Path(request.report_file) if request.report_file else default_report

    try:
        report = await run_enrichment(
            apply=request.apply,
            min_score=request.min_score,
            force_description=request.force_description,
            download_images=request.download_images,
            limit=request.limit,
            report_file=report_path,
        )
        return {
            "message": "Property enrichment completed",
            "mode": "apply" if request.apply else "dry-run",
            "report_file": str(report_path),
            "summary": {
                "baseline_before": report.get("baseline_before"),
                "baseline_after": report.get("baseline_after"),
                "updated": report.get("updated"),
                "skipped_no_match": report.get("skipped_no_match"),
                "skipped_low_score": report.get("skipped_low_score"),
            },
            "samples": report.get("samples", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Property enrichment failed: {e}")


@router.get("/property-enrichment/reports")
async def list_property_enrichment_reports(limit: int = 20):
    """List available property enrichment report files (newest first)."""
    reports_dir = _enrichment_reports_dir()
    if not reports_dir.exists():
        return {"reports": []}

    files = [
        p
        for p in reports_dir.glob("property_enrichment_report*.json")
        if p.is_file() and _is_enrichment_report_filename(p.name)
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    report_items = []
    for p in files[: max(1, min(limit, 200))]:
        st = p.stat()
        report_items.append(
            {
                "filename": p.name,
                "size_bytes": st.st_size,
                "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            }
        )

    return {"reports": report_items}


@router.get("/property-enrichment/reports/{filename}")
async def get_property_enrichment_report(filename: str):
    """Fetch one property enrichment report file by filename."""
    path = _safe_report_path(filename)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        return {"filename": path.name, "report": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {e}")

async def process_batch_geocoding(db: AsyncSession):
    # This logic would ideally be in a service or Celery task.
    # For now, running inline or background (needs careful session handling).
    # Since background tasks with async session can be tricky in FastAPI if not detached properly,
    # we will just run it and hope for the best or assume it's triggered synchronously.
    pass

@router.post("/geocoding/batch")
async def batch_geocode_properties(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Find properties without coordinates and attempt to geocode them via Kartverket.
    """
    # 1. properties missing lat/lon
    result = await db.execute(
        select(Property).where(
            (Property.latitude.is_(None)) | (Property.longitude.is_(None))
        )
    )
    properties = result.scalars().all()
    
    if not properties:
        return {
            "message": "Ingen eiendommer manglet koordinater.", 
            "processed": 0, 
            "total_attempted": 0, 
            "details": []
        }
    
    # 2. Geocode (address + city for better match; rate-limit to avoid Kartverket throttle)
    import asyncio
    client = KartverketClient()
    updated_count = 0
    report_details = []
    
    for prop in properties:
        try:
            prop_name = prop.name if hasattr(prop, 'name') and prop.name else prop.address
            if not prop.address:
                report_details.append({
                    "property_id": str(prop.property_id),
                    "property_name": prop_name or str(prop.property_id),
                    "address": "Mangler adresse",
                    "status": "error",
                    "message": "Ingen adresse registrert på eiendommen",
                    "latitude": None,
                    "longitude": None
                })
                continue

            address_str = f"{prop.address}, {prop.city}" if prop.city else prop.address
            coords = await client.search_address(
                prop.address,
                city=prop.city,
                postal_code=prop.postal_code,
            )

            if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
                lat_val = float(coords["latitude"])
                lon_val = float(coords["longitude"])
                prop.latitude = lat_val
                prop.longitude = lon_val
                updated_count += 1
                report_details.append({
                    "property_id": str(prop.property_id),
                    "property_name": prop_name,
                    "address": address_str,
                    "status": "success",
                    "message": f"Koordinater funnet ({round(lat_val, 4)}, {round(lon_val, 4)})",
                    "latitude": lat_val,
                    "longitude": lon_val
                })
            else:
                 report_details.append({
                    "property_id": str(prop.property_id),
                    "property_name": prop_name,
                    "address": address_str,
                    "status": "warning",
                    "message": "Fant ikke koordinater i Kartverket",
                    "latitude": None,
                    "longitude": None
                })
                 
            await asyncio.sleep(0.15)  # ~6–7 req/s to avoid rate limit
        except Exception as e:
            report_details.append({
                "property_id": str(prop.property_id),
                "property_name": str(prop.name if hasattr(prop, 'name') and prop.name else prop.address) or str(prop.property_id),
                "address": str(getattr(prop, 'address', 'Ukjent')),
                "status": "error",
                "message": f"Feil under geokoding: {str(e)}",
                "latitude": None,
                "longitude": None
            })

        
    await db.commit()
    
    return {
        "message": f"Geokoding ferdig. Suksess på {updated_count} av {len(properties)} adresser.",
        "processed": updated_count,
        "total_attempted": len(properties),
        "details": report_details
    }

@router.post("/risk/batch")
async def batch_calculate_risks(
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger batch calculation of risk for all properties.
    """
    from app.domains.hms.services.risk_service import RiskService
    result = await RiskService.batch_update_risks(db)
    return result


@router.get("/stats/system")
async def system_stats(db: AsyncSession = Depends(get_db)):
    """
    Get system health stats.
    """
    from sqlalchemy import text
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except:
        db_status = "error"
        
    return {
        "database": db_status,
        "external_apis": {
             "nve": "unknown", # Could implement health check call
             "kartverket": "online"
        }
    }

from app.services.data_health_service import data_health_service

@router.get("/health/full")
async def full_data_health_check(db: AsyncSession = Depends(get_db)):
    """
    Performs a comprehensive data integrity check.
    Returns counts, stats, and integrity issues.
    """
    stats = await data_health_service.get_data_stats(db)
    integrity = await data_health_service.check_integrity(db)
    
    return {
        "connectivity": "online" if stats.get("status") != "error" else "offline",
        "volume": stats,
        "integrity": integrity
    }

@router.get("/handbook")
async def get_admin_handbook():
    """
    Returns the content of the Admin Handbook.
    """
    import os
    try:
        # Assuming the docs are in the root/docs folder relative to backend
        # Adjust path as necessary. 
        # Backend runs in /Users/frank/BEFS3/KNOWME/backend
        # Docs are in /Users/frank/BEFS3/KNOWME/docs
        
        file_path = "../../docs/ADMIN_HANDBOOK.md"
        
        if not os.path.exists(file_path):
             # Fallback absolute path attempt
            file_path = "/Users/frank/BEFS3/KNOWME/docs/ADMIN_HANDBOOK.md"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
        else:
             return {"content": "# Fant ikke håndboken\nFilen mangler."}
             
    except Exception as e:
        return {"content": f"# Feil ved lesing\n{str(e)}"}

@router.get("/economic-status")
async def economic_status(db: AsyncSession = Depends(get_db)):
    """
    Returns current row counts and coverage stats for all economic data tables.
    """
    from sqlalchemy import func, distinct
    from app.models.financial_models import Budget, GLTransaction
    from app.models.text_content import TextContent
    from app.models.socioeconomic import SocioeconomicData

    # GL Transactions
    gl_result = await db.execute(
        select(func.count(GLTransaction.transaction_id), func.min(GLTransaction.period), func.max(GLTransaction.period))
    )
    gl_count, gl_min_period, gl_max_period = gl_result.one()

    # Budget
    budget_result = await db.execute(
        select(func.count(Budget.budget_id), func.array_agg(distinct(Budget.year)))
    )
    budget_count, budget_years = budget_result.one()

    # Text content
    text_result = await db.execute(select(func.count(TextContent.text_id)))
    text_count = text_result.scalar()

    # Socioeconomic
    socio_result = await db.execute(select(func.count(SocioeconomicData.socio_data_id)))
    socio_count = socio_result.scalar()

    # Property coverage
    total_props_result = await db.execute(select(func.count(Property.property_id)))
    total_properties = total_props_result.scalar()

    props_with_gl_result = await db.execute(
        select(func.count(distinct(GLTransaction.property_id)))
    )
    props_with_gl = props_with_gl_result.scalar()

    # Top 5 properties by transaction count
    top_props_result = await db.execute(
        select(GLTransaction.property_id, func.count(GLTransaction.transaction_id).label("tx_count"))
        .group_by(GLTransaction.property_id)
        .order_by(func.count(GLTransaction.transaction_id).desc())
        .limit(5)
    )
    top_rows = top_props_result.all()

    # Resolve property names
    top_properties = []
    for prop_id, tx_count in top_rows:
        prop_result = await db.execute(select(Property.name).where(Property.property_id == prop_id))
        prop_name = prop_result.scalar() or str(prop_id)
        top_properties.append({"property_name": prop_name, "transaction_count": tx_count})

    return {
        "gl_transactions": {
            "count": gl_count or 0,
            "min_period": gl_min_period,
            "max_period": gl_max_period,
        },
        "budget": {
            "count": budget_count or 0,
            "years_covered": sorted([y for y in (budget_years or []) if y]) if budget_years else [],
        },
        "text_content": {"count": text_count or 0},
        "socioeconomic_data": {"count": socio_count or 0},
        "property_coverage": {
            "total_properties": total_properties or 0,
            "properties_with_gl_data": props_with_gl or 0,
            "properties_without_gl_data": (total_properties or 0) - (props_with_gl or 0),
        },
        "top_properties_by_transactions": top_properties,
    }


from app.domains.core.models.audit import AuditLog

@router.get("/logs")
async def get_audit_logs(
    limit: int = 50, 
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the latest audit logs.
    """
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    )
    return result.scalars().all()
