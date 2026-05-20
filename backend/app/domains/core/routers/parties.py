import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.core.property_access import get_user_accessible_property_ids

logger = logging.getLogger(__name__)
from app.domains.core.models.party import Party as PartyModel
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.unit import Unit as UnitModel
from app.domains.core.models.property import Property as PropertyModel
from app.domains.core.models.user import User
from app.schemas.property import Party as PartySchema, PartyCreate
from app.services.company_summary_web_llm import fetch_company_summary_via_web_llm
from app.services.due_diligence_service import run_due_diligence
from app.services.external.brreg_service import BrregService
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()


class CompanySummaryResponse(BaseModel):
    summary: str
    saved: bool


class DueDiligenceResponse(BaseModel):
    risk_level: str
    summary: str
    red_flags: list[str]
    detailed_analysis: dict
    follow_up_questions: list[str]
    sources: list[dict]


@router.post("", response_model=PartySchema, status_code=201)
async def create_party(
    party_in: PartyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opprett ny part (leietaker/eier)."""
    db_obj = PartyModel(
        party_id=uuid4(),
        name=party_in.name,
        orgnr=party_in.orgnr,
        contact_email=party_in.contact_email,
        contact_phone=party_in.contact_phone,
        created_at=datetime.utcnow()
    )
    try:
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Part med dette organisasjonsnummeret finnes allerede")

class PropertyMinimal(BaseModel):
    """Minimal eiendomsdata for leietaker-kort."""
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TenantWithPropertySchema(PartySchema):
    """Part/leietaker med tilhørende eiendom (fra aktiv kontrakt)."""
    property: Optional[PropertyMinimal] = None


@router.get("", response_model=list[PartySchema])
async def get_parties(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent alle parter (med paginering) inkl. health_score."""
    from app.services.party_health_service import compute_health_score
    result = await db.execute(select(PartyModel).offset(skip).limit(limit))
    parties = result.scalars().all()
    out = []
    for p in parties:
        schema = PartySchema.model_validate(p)
        schema = schema.model_copy(update={"health_score": compute_health_score(p.external_data)})
        out.append(schema)
    return out


@router.get("/tenants-with-property", response_model=list[TenantWithPropertySchema])
async def get_tenants_with_property(
    skip: int = Query(0, description="Antall å hoppe over (pagination)"),
    limit: int = Query(50, ge=1, le=200, description="Antall å hente (pagination)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent leietakere (parter) med eiendomsinfo i én spørring.
    Reduserer last ved å unngå separate kall til /parties og /contracts.
    Filtreres basert på property access.
    """
    from app.services.party_health_service import compute_health_score

    accessible_ids = await get_user_accessible_property_ids(db, current_user)

    # Hent parter som har minst én aktiv kontrakt på tilgjengelig eiendom
    # Party -> Contract (party_id, status=active) -> Unit -> Property
    stmt = (
        select(PartyModel)
        .join(ContractModel, ContractModel.party_id == PartyModel.party_id)
        .join(UnitModel, UnitModel.unit_id == ContractModel.unit_id)
        .where(ContractModel.status == "active")
        .where(ContractModel.unit_id.isnot(None))
        .distinct(PartyModel.party_id)
    )
    if accessible_ids is not None:
        stmt = stmt.where(UnitModel.property_id.in_(accessible_ids))

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    parties = result.scalars().all()

    if not parties:
        return []

    party_ids = [p.party_id for p in parties]

    # Hent én kontrakt per part (med property) for eiendomsinfo
    # Subquery: for hver party_id, hent contract med unit.property
    contract_stmt = (
        select(ContractModel, PropertyModel)
        .join(UnitModel, UnitModel.unit_id == ContractModel.unit_id)
        .join(PropertyModel, PropertyModel.property_id == UnitModel.property_id)
        .where(ContractModel.party_id.in_(party_ids))
        .where(ContractModel.status == "active")
        .where(ContractModel.unit_id.isnot(None))
    )
    if accessible_ids is not None:
        contract_stmt = contract_stmt.where(UnitModel.property_id.in_(accessible_ids))

    contract_result = await db.execute(contract_stmt)
    rows = contract_result.all()

    # Map party_id -> PropertyMinimal (første treff per party)
    party_to_property: dict[UUID, PropertyMinimal] = {}
    for row in rows:
        contract, prop = row
        pid = contract.party_id
        if pid and pid not in party_to_property and prop:
            party_to_property[pid] = PropertyMinimal(
                name=prop.name,
                address=prop.address,
                latitude=prop.latitude,
                longitude=prop.longitude,
            )

    out = []
    for p in parties:
        schema = PartySchema.model_validate(p)
        schema = schema.model_copy(update={"health_score": compute_health_score(p.external_data)})
        prop = party_to_property.get(p.party_id)
        out.append(TenantWithPropertySchema(**schema.model_dump(), property=prop))
    return out


@router.get("/{party_id}", response_model=PartySchema)
async def get_party(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent en spesifikk part (med antall aktive kontrakter for Smart Insight)."""
    result = await db.execute(select(PartyModel).where(PartyModel.party_id == party_id))
    party = result.scalar_one_or_none()
    if not party:
        raise HTTPException(status_code=404, detail="Part ikke funnet")
    count_stmt = select(func.count(ContractModel.contract_id)).where(
        ContractModel.party_id == party_id,
        ContractModel.status == "active",
    )
    active_count = (await db.execute(count_stmt)).scalar() or 0
    from app.services.party_health_service import compute_health_score
    schema = PartySchema.model_validate(party)
    return schema.model_copy(update={
        "active_contract_count": active_count,
        "health_score": compute_health_score(party.external_data),
    })


@router.post("/{party_id}/enrich-brreg", response_model=PartySchema)
async def enrich_party_brreg(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent BRREG-data (enhet + roller) for partiet og lagre i external_data.
    Krever at partiet har gyldig orgnr (9 siffer).
    """
    result = await db.execute(select(PartyModel).where(PartyModel.party_id == party_id))
    party = result.scalar_one_or_none()
    if not party:
        raise HTTPException(status_code=404, detail="Part ikke funnet")
    orgnr = (party.orgnr or "").strip().replace(" ", "")
    if len(orgnr) != 9 or not orgnr.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Partiet har ikke gyldig orgnr (9 siffer). Kun partier med orgnr kan berikes med BRREG.",
        )
    try:
        enhet = await BrregService.get_enhet(orgnr, db=db)
    except Exception as e:
        logger.exception("BrregService.get_enhet failed for orgnr=%s: %s", orgnr, e)
        raise HTTPException(
            status_code=503,
            detail=f"Kunne ikke hente data fra Brønnøysundregistrene. Prøv igjen senere. ({type(e).__name__})",
        )
    if not enhet:
        # Sjekk om BRREG er tilgjengelig – hvis ikke, gi 503 i stedet for 404
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(
                    "https://data.brreg.no/enhetsregisteret/api/enheter/984851006",
                    headers={"Accept": "application/json", "User-Agent": "BEFS-Eiendomsforvaltning/1.0"},
                )
                if r.status_code != 200:
                    raise HTTPException(
                        status_code=503,
                        detail="Brønnøysundregistrene svarer ikke som forventet. Prøv igjen senere.",
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("BRREG connectivity check failed: %s", e)
            raise HTTPException(
                status_code=503,
                detail="Kunne ikke nå Brønnøysundregistrene. Sjekk internettilkobling eller prøv igjen senere.",
            )
        raise HTTPException(
            status_code=404,
            detail="Ingen BRREG-data funnet for dette organisasjonsnummeret. Sjekk at orgnr er korrekt.",
        )
    try:
        ext = dict(party.external_data or {})
        ext["brreg_enhet"] = enhet
        if enhet.get("respons_klasse") != "SlettetEnhet":
            roller = await BrregService.get_roller(orgnr)
            if roller:
                ext["brreg_roller"] = roller
                roles_list = roller.get("roller") or []
                roles = {}
                for r in roles_list:
                    rt = (r.get("rolletype") or "")
                    if isinstance(rt, dict):
                        rt = (rt.get("beskrivelse") or rt.get("kode") or "")
                    rt = str(rt).lower()
                    navn = r.get("navn") or ""
                    if isinstance(r.get("person"), dict) and isinstance(r["person"].get("navn"), dict):
                        n = r["person"]["navn"]
                        navn = f"{n.get('fornavn', '')} {n.get('etternavn', '')}".strip()
                    if not navn:
                        continue
                    if "daglig" in rt and not roles.get("dagligLeder"):
                        roles["dagligLeder"] = navn
                    elif ("styreleder" in rt or ("styre" in rt and "leder" in rt)) and not roles.get("styretsLeder"):
                        roles["styretsLeder"] = navn
                    elif "revisor" in rt and not roles.get("revisor"):
                        roles["revisor"] = navn
                if roles:
                    ext["roles"] = roles
        party.external_data = ext
        flag_modified(party, "external_data")
        await db.commit()
        await db.refresh(party)
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to save BRREG data for party %s: %s", party_id, e)
        raise HTTPException(
            status_code=503,
            detail=f"Kunne ikke lagre BRREG-data. Prøv igjen senere. ({type(e).__name__})",
        )
    count_stmt = select(func.count(ContractModel.contract_id)).where(
        ContractModel.party_id == party_id,
        ContractModel.status == "active",
    )
    active_count = (await db.execute(count_stmt)).scalar() or 0
    schema = PartySchema.model_validate(party)
    return schema.model_copy(update={"active_contract_count": active_count})


@router.post("/batch-enrich-brreg")
async def batch_enrich_all_brreg(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Kjør BRREG-berikelse for alle parter med orgnr som mangler brreg_enhet data.
    Kjøres i bakgrunnen. Kun for admin.
    """
    import asyncio
    from app.db.session import SessionLocal

    async def _run():
        async with SessionLocal() as db_:
            from sqlalchemy import select as sa_select
            result = await db_.execute(
                sa_select(PartyModel).where(PartyModel.orgnr.isnot(None))
            )
            parties = result.scalars().all()
            candidates = [
                p for p in parties
                if p.orgnr and len(p.orgnr.strip()) == 9
                and not (p.external_data or {}).get("brreg_enhet")
            ]
            logger.info("batch_enrich_brreg: %d parties to enrich", len(candidates))
            done = errors = 0
            for party in candidates:
                try:
                    orgnr = party.orgnr.strip()
                    enhet = await BrregService.get_enhet(orgnr)
                    if enhet:
                        ext = dict(party.external_data or {})
                        ext["brreg_enhet"] = enhet
                        # Also fetch roles for non-deleted companies
                        if enhet.get("respons_klasse") != "SlettetEnhet":
                            try:
                                roller = await BrregService.get_roller(orgnr)
                                if roller:
                                    ext["brreg_roller"] = roller
                                    roles_list = roller.get("roller") or []
                                    roles = {}
                                    for r in roles_list:
                                        rt = (r.get("rolletype") or "")
                                        if isinstance(rt, dict):
                                            rt = (rt.get("beskrivelse") or rt.get("kode") or "")
                                        rt = str(rt).lower()
                                        navn = r.get("navn") or ""
                                        if isinstance(r.get("person"), dict) and isinstance(r["person"].get("navn"), dict):
                                            n = r["person"]["navn"]
                                            navn = f"{n.get('fornavn', '')} {n.get('etternavn', '')}".strip()
                                        if not navn:
                                            continue
                                        if "daglig" in rt and not roles.get("dagligLeder"):
                                            roles["dagligLeder"] = navn
                                        elif ("styreleder" in rt or ("styre" in rt and "leder" in rt)) and not roles.get("styretsLeder"):
                                            roles["styretsLeder"] = navn
                                        elif "revisor" in rt and not roles.get("revisor"):
                                            roles["revisor"] = navn
                                    if roles:
                                        ext["roles"] = roles
                            except Exception:
                                pass  # roller er ikke kritisk
                        party.external_data = ext
                        flag_modified(party, "external_data")
                        done += 1
                    else:
                        errors += 1
                except Exception as e:
                    logger.debug("batch_enrich_brreg: failed %s: %s", party.orgnr, e)
                    errors += 1
                # Commit every 10 + rate-limit
                if (done + errors) % 10 == 0:
                    await db_.commit()
                    await asyncio.sleep(1)  # rate-limit mot BRREG
            await db_.commit()
            logger.info("batch_enrich_brreg: done=%d errors=%d", done, errors)

    background_tasks.add_task(_run)
    return {"status": "started", "message": "BRREG-berikelse kjøres i bakgrunnen for alle parter."}


@router.post("/{party_id}/company-summary-from-web", response_model=CompanySummaryResponse)
async def fetch_party_company_summary_from_web(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent firmaoppsummering via internett-søk (DuckDuckGo) + LLM (OpenAI).
    Søker på firmanavn + orgnr, lager strukturert oppsummering, lagrer i party.external_data['openai_company_summary'].
    Krever OPENAI_API_KEY.
    """
    result = await db.execute(select(PartyModel).where(PartyModel.party_id == party_id))
    party = result.scalar_one_or_none()
    if not party:
        raise HTTPException(status_code=404, detail="Part ikke funnet")
    orgnr = (party.orgnr or "").strip().replace(" ", "")
    if len(orgnr) != 9 or not orgnr.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Partiet har ikke gyldig orgnr (9 siffer). Kun partier med orgnr kan berikes med web-søk.",
        )
    name = (party.name or "").strip()
    ext = party.external_data or {}
    brreg_enhet = ext.get("brreg_enhet") or {}
    brreg_roller = ext.get("brreg_roller")
    brreg_data = dict(brreg_enhet)
    if brreg_roller:
        brreg_data["brreg_roller"] = brreg_roller

    summary, reason = await fetch_company_summary_via_web_llm(
        name, orgnr, max_search_results=5, return_reason=True, brreg_data=brreg_data if brreg_data else None
    )
    if not summary:
        raise HTTPException(
            status_code=503,
            detail=reason or "Kunne ikke hente oppsummering.",
        )
    ext = dict(party.external_data or {})
    ext["openai_company_summary"] = summary
    party.external_data = ext
    flag_modified(party, "external_data")
    await db.commit()
    await db.refresh(party)
    return CompanySummaryResponse(summary=summary, saved=True)


@router.post("/{party_id}/due-diligence", response_model=DueDiligenceResponse)
async def run_party_due_diligence(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kjør Commercial Due Diligence / risikovurdering for partiet.
    Multi-query websøk (konkurs, rettssak, svindel, erfaringer, regnskapstall, daglig leder) + LLM-analyse.
    Lagrer rapport i party.external_data['due_diligence_report']. Krever OPENAI_API_KEY.
    """
    result = await db.execute(select(PartyModel).where(PartyModel.party_id == party_id))
    party = result.scalar_one_or_none()
    if not party:
        raise HTTPException(status_code=404, detail="Part ikke funnet")
    orgnr = (party.orgnr or "").strip().replace(" ", "")
    if len(orgnr) != 9 or not orgnr.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Partiet har ikke gyldig orgnr (9 siffer). Kun partier med orgnr kan vurderes.",
        )
    name = (party.name or "").strip()
    ext = party.external_data or {}
    brreg_enhet = ext.get("brreg_enhet") or {}
    brreg_roller = ext.get("brreg_roller")
    brreg_data = dict(brreg_enhet)
    if brreg_roller:
        brreg_data["brreg_roller"] = brreg_roller

    report, reason = await run_due_diligence(
        name, orgnr, brreg_data=brreg_data if brreg_data else None, return_reason=True
    )
    if report is None:
        raise HTTPException(
            status_code=503,
            detail=reason or "Kunne ikke kjøre risikovurdering.",
        )

    ext["due_diligence_report"] = {
        **report,
        "assessed_at": datetime.utcnow().isoformat() + "Z",
    }
    party.external_data = ext
    flag_modified(party, "external_data")
    await db.commit()
    await db.refresh(party)

    return DueDiligenceResponse(**report)


@router.patch("/{party_id}", response_model=PartySchema)
async def patch_party(
    party_id: UUID,
    party_in: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Oppdater part."""
    result = await db.execute(select(PartyModel).where(PartyModel.party_id == party_id))
    party = result.scalar_one_or_none()
    if not party:
        raise HTTPException(status_code=404, detail="Part ikke funnet")
    
    for field, value in party_in.items():
        if hasattr(party, field) and field not in ('party_id', 'created_at'):
            setattr(party, field, value)
    
    await db.commit()
    await db.refresh(party)
    return party


@router.delete("/{party_id}", status_code=204)
async def delete_party(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Slett part."""
    result = await db.execute(select(PartyModel).where(PartyModel.party_id == party_id))
    party = result.scalar_one_or_none()
    if not party:
        raise HTTPException(status_code=404, detail="Part ikke funnet")

    await db.delete(party)
    await db.commit()
    return Response(status_code=204)


@router.get("/arkiv/inaktive")
async def get_inaktive_parter(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Parter som IKKE har noen aktive kontrakter (kun terminated/expired).
    Brukes til arkiv-visning.
    """
    from sqlalchemy import text as sa_text
    try:
        res = await db.execute(sa_text("""
            SELECT
                p.party_id::text,
                p.name,
                p.orgnr,
                p.contact_email,
                p.created_at::text,
                COUNT(c.contract_id)                                  AS antall_kontrakter,
                MAX(c.end_date::text)                                 AS siste_sluttdato,
                string_agg(DISTINCT c.status, ', ')                   AS statuser,
                string_agg(DISTINCT prop.name, ', ')                  AS eiendommer,
                SUM(
                    CASE
                        WHEN c.amount IS NOT NULL
                             AND jsonb_typeof(c.amount) = 'object'
                             AND (c.amount->>'annual_rent') IS NOT NULL
                        THEN (c.amount->>'annual_rent')::numeric
                        ELSE 0
                    END
                )                                                      AS total_husleie,
                p.external_data
            FROM parties p
            LEFT JOIN contracts c       ON c.party_id  = p.party_id
            LEFT JOIN units u           ON u.unit_id   = c.unit_id
            LEFT JOIN properties prop   ON prop.property_id = u.property_id
            GROUP BY p.party_id, p.name, p.orgnr, p.contact_email, p.created_at, p.external_data
            HAVING BOOL_AND(c.status IS NULL OR c.status != 'active')
            ORDER BY MAX(c.end_date) DESC NULLS LAST, p.name
        """))
        rows = res.mappings().all()
        result = []
        for row in rows:
            ext = row["external_data"] or {}
            brreg = ext.get("brreg_enhet") or {}
            result.append({
                "party_id": row["party_id"],
                "name": row["name"],
                "orgnr": row["orgnr"],
                "contact_email": row["contact_email"],
                "created_at": row["created_at"],
                "antall_kontrakter": int(row["antall_kontrakter"] or 0),
                "siste_sluttdato": row["siste_sluttdato"],
                "statuser": row["statuser"] or "",
                "eiendommer": row["eiendommer"] or "",
                "total_husleie": float(row["total_husleie"] or 0),
                "brreg_navn": brreg.get("navn"),
                "konkurs_flagg": bool(brreg.get("konkurs") or brreg.get("underKonkursbehandling")),
            })
        return {"antall": len(result), "parter": result}
    except Exception as e:
        await db.rollback()
        logger.exception("arkiv/inaktive feilet: %s", e)
        raise HTTPException(status_code=500, detail=f"Feil: {e}")


class BulkDeaktiverRequest(BaseModel):
    party_ids: list[str]


@router.post("/arkiv/reaktiver")
async def reaktiver_kontrakter(
    body: BulkDeaktiverRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sett terminated kontrakter tilbake til 'active' for valgte parter.
    """
    from sqlalchemy import text as sa_text
    from uuid import UUID as _UUID

    if not body.party_ids:
        return {"reaktivert": 0, "parter": 0}

    try:
        uuids = [_UUID(pid) for pid in body.party_ids]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ugyldig party_id: {e}")

    try:
        res = await db.execute(
            sa_text("""
                UPDATE contracts
                SET status = 'active'
                WHERE party_id = ANY(:ids)
                  AND status = 'terminated'
                RETURNING contract_id
            """),
            {"ids": uuids},
        )
        reaktivert = len(res.fetchall())
        await db.commit()
        return {"reaktivert": reaktivert, "parter": len(uuids)}
    except Exception as e:
        await db.rollback()
        logger.exception("reaktiver feilet: %s", e)
        raise HTTPException(status_code=500, detail=f"Reaktivering feilet: {e}")


@router.get("/ikke-i-okonomi/rapport")
async def get_parties_ikke_i_okonomi(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rapport: parter med aktive kontrakter som IKKE finnes i økonomiavdelingens
    regnskap 2025 (finance_budget WHERE data_source = 'kontant_2025').

    Disse partene/leietakerne betaler trolig ikke husleie i 2025 og bør
    vurderes for deaktivering.
    """
    from sqlalchemy import text as sa_text
    try:
        res = await db.execute(sa_text("""
            SELECT
                p.party_id::text,
                p.name,
                p.orgnr,
                p.contact_email,
                p.external_data,
                COUNT(DISTINCT c.contract_id)                       AS antall_kontrakter,
                SUM(
                    CASE
                        WHEN c.amount IS NOT NULL
                             AND jsonb_typeof(c.amount) = 'object'
                             AND (c.amount->>'annual_rent') IS NOT NULL
                        THEN (c.amount->>'annual_rent')::numeric
                        ELSE 0
                    END
                )                                                    AS total_husleie,
                string_agg(DISTINCT prop.name, ', ')                AS eiendommer,
                string_agg(DISTINCT c.status, ', ')                 AS kontrakt_statuser,
                MAX(c.end_date::text)                               AS siste_sluttdato,
                -- Sjekk om parten finnes i kontant_2025 via kontrakter → units → finance_budget
                BOOL_OR(
                    EXISTS (
                        SELECT 1 FROM finance_budget fb
                        WHERE fb.data_source = 'kontant_2025'
                          AND fb.property_id = u2.property_id
                    )
                ) AS er_i_okonomi_2025
            FROM parties p
            JOIN contracts c       ON c.party_id  = p.party_id
            JOIN units u2          ON u2.unit_id   = c.unit_id
            JOIN properties prop   ON prop.property_id = u2.property_id
            WHERE c.status = 'active'
            GROUP BY p.party_id, p.name, p.orgnr, p.contact_email, p.external_data
            HAVING BOOL_OR(
                EXISTS (
                    SELECT 1 FROM finance_budget fb
                    WHERE fb.data_source = 'kontant_2025'
                      AND fb.property_id = u2.property_id
                )
            ) = false
            ORDER BY p.name
        """))
        rows = res.mappings().all()
        result = []
        for row in rows:
            ext = row["external_data"] or {}
            brreg = ext.get("brreg_enhet") or {}
            konkurs = brreg.get("konkurs", False) or brreg.get("underKonkursbehandling", False)
            result.append({
                "party_id": row["party_id"],
                "name": row["name"],
                "orgnr": row["orgnr"],
                "contact_email": row["contact_email"],
                "antall_kontrakter": int(row["antall_kontrakter"] or 0),
                "total_husleie": float(row["total_husleie"] or 0),
                "eiendommer": row["eiendommer"] or "",
                "kontrakt_statuser": row["kontrakt_statuser"] or "",
                "siste_sluttdato": row["siste_sluttdato"],
                "er_i_okonomi_2025": False,
                "konkurs_flagg": bool(konkurs),
                "brreg_navn": brreg.get("navn"),
            })
        return {"antall": len(result), "parter": result}
    except Exception as e:
        await db.rollback()
        logger.exception("ikke-i-okonomi rapport feilet: %s", e)
        raise HTTPException(status_code=500, detail=f"Rapport feilet: {e}")


@router.post("/ikke-i-okonomi/deaktiver-bulk")
async def deaktiver_parter_bulk(
    body: BulkDeaktiverRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sett alle aktive kontrakter for de angitte partene til 'terminated'.
    Brukes for å deaktivere parter som ikke finnes i økonomiregnskapet 2025.
    """
    from sqlalchemy import text as sa_text, update
    from uuid import UUID as _UUID

    if not body.party_ids:
        return {"deaktivert": 0, "parter": 0}

    try:
        uuids = [_UUID(pid) for pid in body.party_ids]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ugyldig party_id: {e}")

    try:
        res = await db.execute(
            sa_text("""
                UPDATE contracts
                SET status = 'terminated'
                WHERE party_id = ANY(:ids)
                  AND status = 'active'
                RETURNING contract_id
            """),
            {"ids": uuids},
        )
        deaktivert = len(res.fetchall())
        await db.commit()
        return {"deaktivert": deaktivert, "parter": len(uuids)}
    except Exception as e:
        await db.rollback()
        logger.exception("bulk deaktiver feilet: %s", e)
        raise HTTPException(status_code=500, detail=f"Deaktivering feilet: {e}")
