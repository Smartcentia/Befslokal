"""API endpoints for deviations (Avvik) using InternalControlCase."""
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
import base64
import json
import os

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.core.property_access import check_property_access, get_user_accessible_property_ids
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.property import Property
from app.models.file_meta import FileMeta
from app.services.storage import get_storage
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

class DeviationCreate(BaseModel):
    title: str
    description: str
    property_id: str
    priority: str = "medium"
    due_date: Optional[datetime] = None

class Deviation(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    property_id: str
    property_name: Optional[str] = None
    severity: str # Maps to priority
    created_at: Any
    
    model_config = ConfigDict(from_attributes=True)

class DeviationStats(BaseModel):
    total: int
    open: int
    closed: int
    critical: int
    high: int
    medium: int
    low: int

@router.post("", response_model=Deviation, status_code=status.HTTP_201_CREATED)
async def create_deviation(
    data: DeviationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Opprett et nytt avvik (InternalControlCase type='deviation').
    """
    # Check access
    await check_property_access(db, current_user, data.property_id, require_write=True)

    # Verify property exists
    prop_res = await db.execute(select(Property).where(Property.property_id == data.property_id))
    prop = prop_res.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    case = InternalControlCase(
        property_id=data.property_id,
        title=data.title,
        description=data.description,
        case_type="deviation",
        status="open",
        priority=data.priority.lower(),
        due_date=data.due_date,
        assigned_user_id=current_user.user_id, # Assign to creator initially
        process_state="Opprettet"
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    # Reload with property for response
    # (Actually property is already loaded via lazy='selectin' on model usually, but to be safe)
    return Deviation(
        id=str(case.case_id),
        title=case.title,
        description=case.description,
        status=case.status,
        property_id=str(case.property_id),
        property_name=prop.name or prop.address,
        severity=case.priority,
        created_at=case.created_at
    )

@router.get("", response_model=List[Deviation])
async def get_deviations(
    status: Optional[str] = Query(None, description="Status filter (open, closed, etc)"),
    priority: Optional[str] = Query(None, description="Priority filter"),
    limit: int = Query(50, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent avvik (InternalControlCase type='deviation').
    """
    # Get accessible properties
    accessible_property_ids = await get_user_accessible_property_ids(db, current_user)
    if accessible_property_ids is not None and len(accessible_property_ids) == 0:
        return []

    from sqlalchemy.orm import selectinload
    stmt = select(InternalControlCase).options(
        selectinload(InternalControlCase.property)
    ).where(InternalControlCase.case_type == "deviation")

    # Filter by access
    if accessible_property_ids is not None:
        stmt = stmt.where(InternalControlCase.property_id.in_(accessible_property_ids))

    if status:
        stmt = stmt.where(InternalControlCase.status == status)
    
    if priority:
        stmt = stmt.where(InternalControlCase.priority == priority.lower())

    stmt = stmt.order_by(desc(InternalControlCase.created_at)).limit(limit).offset(offset)

    result = await db.execute(stmt)
    cases = result.scalars().all()

    return [
        Deviation(
            id=str(c.case_id),
            title=c.title,
            description=c.description,
            status=c.status,
            property_id=str(c.property_id),
            property_name=c.property.name if c.property else None,
            severity=c.priority,
            created_at=c.created_at
        )
        for c in cases
    ]

@router.get("/stats", response_model=DeviationStats)
async def get_deviation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for deviations (InternalControlCase type='deviation').
    """
    accessible_property_ids = await get_user_accessible_property_ids(db, current_user)
    if accessible_property_ids is not None and len(accessible_property_ids) == 0:
        return DeviationStats(total=0, open=0, closed=0, critical=0, high=0, medium=0, low=0)

    base_query = select(InternalControlCase).where(InternalControlCase.case_type == "deviation")
    if accessible_property_ids is not None:
        base_query = base_query.where(InternalControlCase.property_id.in_(accessible_property_ids))

    # We could optimize this with a single aggregation query, but for simplicity/readability:
    async def count_where(*filters):
        stmt = select(func.count()).select_from(InternalControlCase).where(InternalControlCase.case_type == "deviation")
        if accessible_property_ids is not None:
            stmt = stmt.where(InternalControlCase.property_id.in_(accessible_property_ids))
        for f in filters:
            stmt = stmt.where(f)
        return (await db.execute(stmt)).scalar() or 0

    total = await count_where()
    open_count = await count_where(InternalControlCase.status == "open")
    closed_count = await count_where(InternalControlCase.status == "closed")
    
    critical = await count_where(func.lower(InternalControlCase.priority) == "critical")
    high = await count_where(func.lower(InternalControlCase.priority) == "high")
    medium = await count_where(func.lower(InternalControlCase.priority) == "medium")
    low = await count_where(func.lower(InternalControlCase.priority) == "low")

    return DeviationStats(
        total=total,
        open=open_count,
        closed=closed_count,
        critical=critical,
        high=high,
        medium=medium,
        low=low
    )

@router.get("/{id}", response_model=Deviation)
async def get_deviation(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent et spesifikt avvik.
    """
    try:
        uuid_id = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    from sqlalchemy.orm import selectinload
    stmt = select(InternalControlCase).where(
        InternalControlCase.case_id == uuid_id,
        InternalControlCase.case_type == "deviation"
    ).options(selectinload(InternalControlCase.property))
    
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Deviation not found")

    # Check access
    await check_property_access(db, current_user, str(case.property_id), require_write=False)

    return Deviation(
        id=str(case.case_id),
        title=case.title,
        description=case.description,
        status=case.status,
        property_id=str(case.property_id),
        property_name=case.property.name if case.property else None,
        severity=case.priority,
        created_at=case.created_at
    )


# ─── Bildevedlegg + KI-vurdering ─────────────────────────────────────────────

class DeviationImageOut(BaseModel):
    file_id: str
    original_filename: Optional[str]
    download_url: str
    created_at: Any

class AiAssessmentResult(BaseModel):
    alvorlighetsgrad: str          # kritisk / høy / middels / lav
    sammendrag: str
    anbefalte_tiltak: List[str]
    estimert_kostnad_nok: Optional[int]

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/{case_id}/images", response_model=DeviationImageOut, status_code=201)
async def upload_deviation_image(
    case_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Last opp et bilde knyttet til et avvik."""
    try:
        uid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(400, "Ugyldig case_id")

    # Hent avviket
    res = await db.execute(select(InternalControlCase).where(InternalControlCase.case_id == uid))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Avvik ikke funnet")
    await check_property_access(db, current_user, str(case.property_id), require_write=True)

    # Valider filtype og størrelse
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(415, f"Filtype ikke støttet: {content_type}. Bruk JPEG, PNG eller WebP.")

    content = await file.read()
    if len(content) > _MAX_IMAGE_BYTES:
        raise HTTPException(413, "Bildet er for stort (maks 10 MB)")

    # Lagre til lokal storage
    ext = (file.filename or "bilde.jpg").rsplit(".", 1)[-1].lower()
    file_id = uuid.uuid4()
    blob_path = f"deviations/{case_id}/{file_id}.{ext}"

    storage = get_storage()
    storage.save_file(blob_path, content)

    # Registrer i FileMeta
    meta = FileMeta(
        file_id=file_id,
        case_id=uid,
        path=blob_path,
        original_filename=file.filename,
        content_type=content_type,
        file_type="image",
        tags=["deviation_image"],
    )
    db.add(meta)
    await db.commit()

    download_url = f"/api/v1/files/{file_id}/download"
    logger.debug("Bilde lastet opp for avvik %s: %s", case_id, blob_path)
    return DeviationImageOut(
        file_id=str(file_id),
        original_filename=file.filename,
        download_url=download_url,
        created_at=meta.created_at,
    )


@router.get("/{case_id}/images", response_model=List[DeviationImageOut])
async def get_deviation_images(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent alle bilder for et avvik."""
    try:
        uid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(400, "Ugyldig case_id")

    res = await db.execute(select(InternalControlCase).where(InternalControlCase.case_id == uid))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Avvik ikke funnet")
    await check_property_access(db, current_user, str(case.property_id), require_write=False)

    img_res = await db.execute(
        select(FileMeta)
        .where(FileMeta.case_id == uid)
        .order_by(FileMeta.created_at)
    )
    images = img_res.scalars().all()

    return [
        DeviationImageOut(
            file_id=str(img.file_id),
            original_filename=img.original_filename,
            download_url=f"/api/v1/files/{img.file_id}/download",
            created_at=img.created_at,
        )
        for img in images
        if img.tags and "deviation_image" in img.tags
    ]


@router.post("/{case_id}/ai-assess", response_model=AiAssessmentResult)
async def ai_assess_deviation(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyser skadebilder for et avvik med GPT-4o vision.
    Returnerer alvorlighetsgrad, sammendrag og anbefalte tiltak.
    """
    try:
        uid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(400, "Ugyldig case_id")

    # Hent avviket
    res = await db.execute(select(InternalControlCase).where(InternalControlCase.case_id == uid))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Avvik ikke funnet")
    await check_property_access(db, current_user, str(case.property_id), require_write=False)

    # Hent bilder
    img_res = await db.execute(
        select(FileMeta)
        .where(FileMeta.case_id == uid)
        .order_by(FileMeta.created_at)
    )
    images = [img for img in img_res.scalars().all() if img.tags and "deviation_image" in img.tags]

    if not images:
        raise HTTPException(422, "Ingen bilder funnet for dette avviket. Last opp minst ett bilde.")

    # Les bildedata og konverter til base64 (maks 4 bilder for å holde token-kostnad nede)
    storage = get_storage()
    image_content_parts = []
    for img in images[:4]:
        try:
            raw = storage.get_file(img.path)
            b64 = base64.b64encode(raw).decode("utf-8")
            mime = img.content_type or "image/jpeg"
            image_content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"},
            })
        except Exception as e:
            logger.warning("Kunne ikke lese bilde %s: %s", img.file_id, e)

    if not image_content_parts:
        raise HTTPException(500, "Kunne ikke lese bildedata fra lagring.")

    # Bygg GPT-4o vision-kall
    from openai import AsyncOpenAI
    from app.core.config import settings

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompt = (
        "Du er en ekspert på bygningsskader og eiendomsforvaltning for Bufetat. "
        "Analyser skadebildet/-bildene og gi en strukturert vurdering på norsk. "
        "Svar KUN med gyldig JSON på dette formatet:\n"
        '{"alvorlighetsgrad": "kritisk|høy|middels|lav", '
        '"sammendrag": "kort beskrivelse av skaden", '
        '"anbefalte_tiltak": ["tiltak 1", "tiltak 2"], '
        '"estimert_kostnad_nok": 50000}'
    )

    avvik_tekst = f"Avvik: {case.title}"
    if case.description:
        avvik_tekst += f"\nBeskrivelse: {case.description}"
    avvik_tekst += f"\nPrioritet: {case.priority}"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": avvik_tekst},
                *image_content_parts,
            ],
        },
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=800,
            temperature=0.2,
        )
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
    except Exception as e:
        logger.error("GPT-4o vision-kall feilet: %s", e)
        raise HTTPException(502, f"KI-analyse feilet: {str(e)}")

    return AiAssessmentResult(
        alvorlighetsgrad=data.get("alvorlighetsgrad", "ukjent"),
        sammendrag=data.get("sammendrag", ""),
        anbefalte_tiltak=data.get("anbefalte_tiltak", []),
        estimert_kostnad_nok=data.get("estimert_kostnad_nok"),
    )
