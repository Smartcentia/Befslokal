"""
SIMBA 2.1 validering – endepunkter for BEFS
────────────────────────────────────────────
POST /fdvu/simba/{property_id}/validate  → valider IFC-fil mot SIMBA 2.1-krav
GET  /fdvu/simba/disciplines             → hent liste over disipliner + regler
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


@router.post("/{property_id}/validate", response_model=Dict[str, Any])
async def validate_simba(
    property_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validerer en IFC-fil mot Statsbygg SIMBA 2.1-kravene for alle 12 disipliner.
    Ingen data skrives til databasen.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Ingen tilgang")

    # Verifiser at eiendommen eksisterer
    from app.domains.core.models.property import Property
    prop = await db.get(Property, uuid.UUID(property_id))
    if not prop:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Filen er for stor (maks 200 MB)")
    if not content:
        raise HTTPException(status_code=400, detail="Tom fil")

    try:
        from app.services.simba_validator import validate_simba as _validate
        result = _validate(content, file.filename or "model.ifc")
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="ifcopenshell er ikke installert på serveren. Legg til i requirements.txt og redeploy.",
        )
    except Exception as exc:
        logger.warning("SIMBA validering feilet for property %s: %s", property_id, exc)
        raise HTTPException(status_code=422, detail=f"Kunne ikke validere IFC-filen: {exc}")

    disciplines_out = []
    for d in result.disciplines:
        rules_out = []
        for r in d.rules:
            rules_out.append({
                "rule_id":     r.rule_id,
                "description": r.description,
                "status":      r.status,
                "passed":      r.passed,
                "failed":      r.failed,
                "total":       r.total,
                "pass_rate":   round(r.pass_rate, 1),
                "failed_guids": r.failed_guids[:10],  # maks 10
            })
        disciplines_out.append({
            "discipline":     d.discipline,
            "label":          d.label,
            "overall_status": d.overall_status,
            "compliance_pct": round(d.compliance_pct, 1),
            "total_rules":    d.total_rules,
            "passed_rules":   d.passed_rules,
            "warn_rules":     d.warn_rules,
            "failed_rules":   d.failed_rules,
            "na_rules":       d.na_rules,
            "rules":          rules_out,
        })

    return {
        "property_id":  property_id,
        "filename":     file.filename,
        "schema":       result.schema,
        "project_name": result.project_name,
        "summary":      result.summary,
        "warnings":     result.warnings,
        "disciplines":  disciplines_out,
    }


@router.get("/disciplines", response_model=Dict[str, Any])
async def list_simba_disciplines(
    current_user: User = Depends(get_current_user),
):
    """Returnerer liste over SIMBA 2.1-disipliner og hva de dekker."""
    return {
        "version": "SIMBA 2.1",
        "ifc_version": "IFC 4 (4.0.2.1)",
        "reference": "https://simba.statsbygg.no/kravene",
        "disciplines": [
            {"code": "RIM",   "label": "BIM-koordinering",      "description": "Grunnkrav for alle disipliner: GUID, Name, Project-informasjon"},
            {"code": "ARK",   "label": "Arkitekt",              "description": "Bygg, etasjer, rom, dører, vinduer"},
            {"code": "LARK",  "label": "Landskapsarkitekt",     "description": "Tomteforhold (IfcSite)"},
            {"code": "IARK",  "label": "Interiørarkitekt",      "description": "Inventar og innredning (IfcFurnishingElement)"},
            {"code": "RIB",   "label": "Konstruksjon",          "description": "Bærende elementer: søyler, bjelker, dekker, vegger"},
            {"code": "RIV",   "label": "VVS",                   "description": "Ventilasjon, varme, sanitær"},
            {"code": "RIVA",  "label": "Vann/avløp",            "description": "Sanitæranlegg (IfcSanitaryTerminal)"},
            {"code": "RIE",   "label": "Elektro",               "description": "Elektrisk utstyr og belysning"},
            {"code": "RIAKU", "label": "Akustikk",              "description": "Lydforhold i rom (Pset_SpaceCommon.AcousticRating)"},
            {"code": "RIBR",  "label": "Brann",                 "description": "Brannbeskyttelse: FireRating på dører og vegger"},
            {"code": "RIS",   "label": "Sikkerhet",             "description": "Sikkerhetsvurdering av dører (SecurityRating)"},
            {"code": "RIEN",  "label": "Energi",                "description": "Energirelaterte egenskaper: GrossPlannedArea, vindusareal, tak"},
        ],
    }
