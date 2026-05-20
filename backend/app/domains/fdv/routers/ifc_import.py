"""
IFC Import – endepunkter for BEFS
──────────────────────────────────
POST /fdvu/ifc/{property_id}/parse   → dry-run, returnerer preview
POST /fdvu/ifc/{property_id}/import  → skriver Building/Floor/Space/BIMObject til DB
GET  /fdvu/ifc/{property_id}/models  → list BIMModel-rader for eiendommen
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


# ─── Hjelpefunksjoner ─────────────────────────────────────────────────────────

async def _get_property(db: AsyncSession, property_id: str):
    from app.domains.core.models.property import Property
    prop = await db.get(Property, uuid.UUID(property_id))
    if not prop:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")
    return prop


def _preview_from_result(result) -> Dict[str, Any]:
    """Bygg preview-dict fra IFCParseResult (uten DB-skriving)."""
    buildings_preview = []
    for b in result.buildings:
        floors_preview = []
        for f in b.floors:
            floors_preview.append({
                "ifc_guid":    f.ifc_guid,
                "name":        f.name,
                "floor_number": f.floor_number,
                "area_sqm":    f.area_sqm,
                "space_count": len(f.spaces),
                "spaces": [
                    {
                        "ifc_guid":   s.ifc_guid,
                        "name":       s.name,
                        "space_type": s.space_type,
                        "area_sqm":   s.area_sqm,
                    }
                    for s in f.spaces[:10]   # maks 10 i preview
                ],
            })
        buildings_preview.append({
            "ifc_guid":     b.ifc_guid,
            "name":         b.name,
            "building_code": b.building_code,
            "year_built":   b.year_built,
            "total_area_sqm": b.total_area_sqm,
            "building_type": b.building_type,
            "floor_count":  len(b.floors),
            "space_count":  sum(len(f.spaces) for f in b.floors),
            "floors":       floors_preview,
        })
    return {
        "schema":       result.schema,
        "project_name": result.project_name,
        "stats":        result.stats,
        "warnings":     result.warnings,
        "buildings":    buildings_preview,
    }


# ─── POST /parse (dry-run) ────────────────────────────────────────────────────

@router.post("/{property_id}/parse", response_model=Dict[str, Any])
async def parse_ifc_preview(
    property_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dry-run: parser IFC-fil og returnerer forhåndsvisning av hva som vil opprettes.
    Ingenting skrives til databasen.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Ingen tilgang")

    await _get_property(db, property_id)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Filen er for stor (maks 200 MB)")
    if not content:
        raise HTTPException(status_code=400, detail="Tom fil")

    try:
        from app.services.ifc_parser import parse_ifc
        result = parse_ifc(content, file.filename or "model.ifc")
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="ifcopenshell er ikke installert på serveren. Legg til i requirements.txt og redeploy."
        )
    except Exception as exc:
        logger.warning("IFC parse feilet for property %s: %s", property_id, exc)
        raise HTTPException(status_code=422, detail=f"Kunne ikke parse IFC-filen: {exc}")

    return {
        "dry_run": True,
        "property_id": property_id,
        "filename": file.filename,
        **_preview_from_result(result),
    }


# ─── POST /import (skriv til DB) ─────────────────────────────────────────────

@router.post("/{property_id}/import", response_model=Dict[str, Any])
async def import_ifc(
    property_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Parser IFC og skriver Building → Floor → Space → BIMObject til DB.
    Konfliktsstrategi: match på navn (case-insensitive), oppdater metadata.
    Lagrer BIMModel-rad med status 'ready'.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Ingen tilgang")

    prop = await _get_property(db, property_id)
    prop_uuid = prop.property_id

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Filen er for stor (maks 200 MB)")

    try:
        from app.services.ifc_parser import parse_ifc
        result = parse_ifc(content, file.filename or "model.ifc")
    except ImportError:
        raise HTTPException(status_code=501, detail="ifcopenshell ikke installert på serveren")
    except Exception as exc:
        logger.warning("IFC import parse-feil for property %s: %s", property_id, exc)
        raise HTTPException(status_code=422, detail=f"Kunne ikke parse IFC-filen: {exc}")

    from app.domains.core.models.building import Building, Floor, Space
    from app.domains.fdv.models.bim import BIMModel, BIMObject

    # ── 1. Lagre BIMModel-rad ─────────────────────────────────────────────────
    bim_model = BIMModel(
        property_id=prop_uuid,
        filename=file.filename or "model.ifc",
        format="IFC",
        status="ready",
        file_path=None,  # ikke lagret på disk
    )
    db.add(bim_model)
    await db.flush()  # gir oss bim_model.model_id

    created = {"buildings": 0, "floors": 0, "spaces": 0, "bim_objects": 0, "updated": 0}

    # ── 2. Bygninger ──────────────────────────────────────────────────────────
    for pb in result.buildings:
        # Match på navn
        existing_b_q = await db.execute(
            select(Building).where(
                Building.property_id == prop_uuid,
                Building.name.ilike(pb.name),
            )
        )
        existing_b = existing_b_q.scalar_one_or_none()

        if existing_b:
            # Oppdater metadata
            if pb.year_built:
                existing_b.year_built = pb.year_built
            if pb.total_area_sqm:
                existing_b.total_area_sqm = pb.total_area_sqm
            if pb.building_code:
                existing_b.building_code = pb.building_code
            building_obj = existing_b
            created["updated"] += 1
        else:
            building_obj = Building(
                property_id=prop_uuid,
                name=pb.name,
                building_code=pb.building_code,
                year_built=pb.year_built,
                total_area_sqm=pb.total_area_sqm,
                building_type=pb.building_type,
                description=f"Importert fra IFC: {result.project_name}",
            )
            db.add(building_obj)
            await db.flush()
            created["buildings"] += 1

        # ── 3. Etasjer ────────────────────────────────────────────────────────
        for pf in pb.floors:
            existing_f_q = await db.execute(
                select(Floor).where(
                    Floor.building_id == building_obj.building_id,
                    Floor.floor_number == pf.floor_number,
                )
            )
            existing_f = existing_f_q.scalar_one_or_none()

            if existing_f:
                if pf.area_sqm:
                    existing_f.area_sqm = pf.area_sqm
                floor_obj = existing_f
                created["updated"] += 1
            else:
                floor_obj = Floor(
                    building_id=building_obj.building_id,
                    floor_number=pf.floor_number,
                    name=pf.name,
                    area_sqm=pf.area_sqm,
                )
                db.add(floor_obj)
                await db.flush()
                created["floors"] += 1

            # ── 4. Rom ────────────────────────────────────────────────────────
            for ps in pf.spaces:
                existing_s_q = await db.execute(
                    select(Space).where(
                        Space.floor_id == floor_obj.floor_id,
                        Space.name.ilike(ps.name),
                    )
                )
                existing_s = existing_s_q.scalar_one_or_none()

                if existing_s:
                    if ps.area_sqm:
                        existing_s.area_sqm = ps.area_sqm
                    created["updated"] += 1
                else:
                    db.add(Space(
                        floor_id=floor_obj.floor_id,
                        property_id=prop_uuid,
                        name=ps.name,
                        space_type=ps.space_type,
                        area_sqm=ps.area_sqm,
                        description=ps.description,
                    ))
                    created["spaces"] += 1

    # ── 5. BIMObjects ─────────────────────────────────────────────────────────
    for po in result.bim_objects[:2000]:   # maks 2000 objekter per import
        db.add(BIMObject(
            model_id=bim_model.model_id,
            ifc_guid=po.ifc_guid,
            name=po.name,
            type=po.ifc_type,
            pos_x=po.pos_x,
            pos_y=po.pos_y,
            pos_z=po.pos_z,
            properties=po.properties,
        ))
        created["bim_objects"] += 1

    await db.commit()

    logger.debug(
        "IFC import for property %s: %s", property_id, created
    )

    return {
        "success": True,
        "property_id": property_id,
        "bim_model_id": str(bim_model.model_id),
        "schema": result.schema,
        "project_name": result.project_name,
        "created": created,
        "warnings": result.warnings,
        "stats": result.stats,
    }


# ─── GET /models ──────────────────────────────────────────────────────────────

@router.get("/{property_id}/models", response_model=Dict[str, Any])
async def list_ifc_models(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent alle importerte BIMModel-rader for en eiendom."""
    await _get_property(db, property_id)
    from app.domains.fdv.models.bim import BIMModel
    prop_uuid = uuid.UUID(property_id)
    result = await db.execute(
        select(BIMModel)
        .where(BIMModel.property_id == prop_uuid)
        .order_by(BIMModel.upload_date.desc())
    )
    models = result.scalars().all()
    return {
        "property_id": property_id,
        "count": len(models),
        "models": [
            {
                "model_id":    str(m.model_id),
                "filename":    m.filename,
                "format":      m.format,
                "status":      m.status,
                "upload_date": m.upload_date.isoformat() if m.upload_date else None,
            }
            for m in models
        ],
    }
