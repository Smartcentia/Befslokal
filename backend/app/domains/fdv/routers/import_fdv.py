"""
FDV-import API
==============
POST /fdvu/import/components-csv  – last opp CSV med bygningskomponenter
POST /fdvu/import/document         – registrer FDV-dokument fra URL/metadata
GET  /fdvu/import/template         – last ned CSV-mal
"""
from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.fdv.models.fdv import BuildingComponent as ComponentModel
from app.domains.fdv.models.compliance import FdvDocument

logger = logging.getLogger(__name__)
router = APIRouter()

# ─────────────────────────────────────────────
# CSV-mal kolonner
# ─────────────────────────────────────────────

CSV_COLUMNS = [
    "name",
    "type",
    "ns3451_code",
    "serial_number",
    "barcode",
    "replacement_year",
    "criticality_level",
    "section_id",
]

# ─────────────────────────────────────────────
# Skjemaer
# ─────────────────────────────────────────────


class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: List[str]


class DocumentImportRequest(BaseModel):
    property_id: str
    title: str
    document_type: str
    external_url: Optional[str] = None
    valid_until: Optional[date] = None
    description: Optional[str] = None
    section_id: Optional[str] = None


class DocumentImportResult(BaseModel):
    document_id: str
    title: str
    document_type: str


# ─────────────────────────────────────────────
# Hjelpefunksjoner
# ─────────────────────────────────────────────


def _safe_str(value: str) -> Optional[str]:
    """Returner None for tomme strenger."""
    stripped = value.strip()
    return stripped if stripped else None


def _parse_int(value: str, field: str) -> Optional[int]:
    """Parse heltall, returner None om tomt, kast ValueError ved ugyldig."""
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return int(stripped)
    except ValueError:
        raise ValueError(f"Ugyldig heltall for '{field}': {stripped!r}")


def _parse_uuid(value: str, field: str) -> Optional[uuid.UUID]:
    """Parse UUID, returner None om tomt."""
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return uuid.UUID(stripped)
    except ValueError:
        raise ValueError(f"Ugyldig UUID for '{field}': {stripped!r}")


# ─────────────────────────────────────────────
# Endepunkter
# ─────────────────────────────────────────────


@router.get("/template")
async def download_csv_template():
    """
    Returner en CSV-mal med alle støttede kolonner.
    Bruk denne som utgangspunkt for masseimport av bygningskomponenter.
    """
    content = ",".join(CSV_COLUMNS) + "\n"
    content += "Ventilasjon tak,HVAC,36,SN-12345,BC-00001,2035,high,\n"

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8-sig")),  # BOM for Excel-kompatibilitet
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=fdv_komponenter_mal.csv"
        },
    )


@router.post("/components-csv", response_model=ImportResult)
async def import_components_csv(
    property_id: uuid.UUID = Query(..., description="Eiendoms-ID komponenter tilhører"),
    file: UploadFile = File(..., description="CSV-fil med komponentdata"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer bygningskomponenter fra CSV-fil.

    Forventede kolonner (se /fdvu/import/template):
    name, type, ns3451_code, serial_number, barcode,
    replacement_year, criticality_level, section_id

    Obligatorisk: name
    Returnerer antall opprettet, hoppet over og eventuelle feil per rad.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Kun CSV-filer er støttet (.csv)"
        )

    raw_bytes = await file.read()

    # Prøv UTF-8 med BOM, fall tilbake til latin-1 (vanlig i norske Excel-eksporter)
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            content = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise HTTPException(
            status_code=400,
            detail="Kunne ikke dekode CSV-filen. Lagre som UTF-8 eller latin-1.",
        )

    reader = csv.DictReader(io.StringIO(content))

    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV-filen er tom eller mangler header.")

    created = 0
    skipped = 0
    errors: List[str] = []

    for row_num, row in enumerate(reader, start=2):  # start=2 fordi rad 1 er header
        name = _safe_str(row.get("name", ""))
        if not name:
            skipped += 1
            continue

        try:
            # Bygg technical_data fra ekstra felter i CSV som ikke er egne kolonner
            technical_data: Dict[str, Any] = {}

            serial = _safe_str(row.get("serial_number", ""))
            if serial:
                technical_data["serial_number"] = serial

            barcode = _safe_str(row.get("barcode", ""))
            if barcode:
                technical_data["barcode"] = barcode

            replacement_year = _parse_int(row.get("replacement_year", ""), "replacement_year")
            if replacement_year is not None:
                technical_data["replacement_year"] = replacement_year

            criticality = _safe_str(row.get("criticality_level", ""))
            if criticality:
                technical_data["criticality_level"] = criticality

            section_id = _parse_uuid(row.get("section_id", ""), "section_id")

            component = ComponentModel(
                property_id=property_id,
                name=name,
                type=_safe_str(row.get("type", "")),
                ns3451_code=_safe_str(row.get("ns3451_code", "")),
                technical_data=technical_data,
                status="active",
            )

            db.add(component)
            created += 1

        except ValueError as exc:
            errors.append(f"Rad {row_num}: {exc}")
        except Exception as exc:
            logger.debug("CSV import feil rad %d: %s", row_num, exc)
            errors.append(f"Rad {row_num}: Uventet feil – {exc}")

    if created > 0:
        try:
            await db.commit()
        except Exception as exc:
            await db.rollback()
            logger.error("CSV import commit feil: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Databasefeil ved lagring: {exc}",
            )

    logger.debug(
        "FDV CSV-import eiendom=%s: created=%d skipped=%d errors=%d",
        property_id,
        created,
        skipped,
        len(errors),
    )
    return ImportResult(created=created, skipped=skipped, errors=errors)


@router.post("/document", response_model=DocumentImportResult)
async def import_fdv_document(
    payload: DocumentImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registrer et FDV-dokument fra URL/metadata (ingen filopplasting).

    Eksempel på document_type: brannplan, fdv_manual, tegning,
    serviceavtale, garantidokument, energiattest, hms_prosedyre.
    """
    try:
        property_uuid = uuid.UUID(payload.property_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig property_id UUID")

    section_uuid: Optional[uuid.UUID] = None
    if payload.section_id:
        try:
            section_uuid = uuid.UUID(payload.section_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Ugyldig section_id UUID")

    doc = FdvDocument(
        property_id=property_uuid,
        title=payload.title,
        document_type=payload.document_type,
        external_url=payload.external_url,
        valid_until=payload.valid_until,
        description=payload.description,
        section_id=section_uuid,
        uploaded_by=current_user.user_id if hasattr(current_user, "user_id") else None,
        status="active",
    )

    try:
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
    except Exception as exc:
        await db.rollback()
        logger.error("FDV dokument import feil: %s", exc)
        raise HTTPException(status_code=500, detail=f"Databasefeil: {exc}")

    logger.debug("FDV dokument registrert: %s (%s)", doc.title, doc.document_id)
    return DocumentImportResult(
        document_id=str(doc.document_id),
        title=doc.title,
        document_type=doc.document_type,
    )
