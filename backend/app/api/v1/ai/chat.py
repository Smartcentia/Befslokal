"""
KI Kollega Chat API Endpoint

Provides a chat interface for the AI assistant with:
- Context-aware responses
- Streaming support (SSE)
- Conversation history
"""

from __future__ import annotations
import json
import re
import asyncio
import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy import text

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.services.intelligence.ki_kollega.service import ki_kollega_service
from app.services.intelligence.fullverdig.service import FullverdigService
from app.core.config import settings

fullverdig_service = FullverdigService()

logger = logging.getLogger(__name__)

# --- Enkel chat: kun OpenAI + våre data i kontekst (ingen graf/verktøy) ---

async def _load_properties_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle eiendommer – ingen grense, KI Kollega skal lese alle data."""
    try:
        result = await db.execute(text("""
            SELECT name, address, city, total_area, region
            FROM properties
            ORDER BY total_area DESC NULLS LAST
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen eiendommer i databasen."
        lines = ["Navn | Adresse | By | Areal (m²) | Region"]
        for r in rows:
            name = (r.name or "-")[:40]
            address = (r.address or "-")[:35]
            city = (r.city or "-")[:20]
            area = f"{r.total_area:.0f}" if r.total_area is not None else "-"
            region = (r.region or "-")[:15]
            lines.append(f"{name} | {address} | {city} | {area} | {region}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste eiendommer: {e}")
        return "Kunne ikke laste eiendomsdata (databasefeil)."


async def _load_all_property_names_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle eiendomsnavn sortert på navn – brukes ved «alle familievernkontor», «finn alle X»."""
    try:
        result = await db.execute(text("""
            SELECT name, region
            FROM properties
            ORDER BY name
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen eiendommer i databasen."
        lines = ["Navn | Region"]
        for r in rows:
            name = (r.name or "-")[:60]
            region = (r.region or "-")[:20]
            lines.append(f"{name} | {region}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste alle eiendomsnavn: {e}")
        return "Kunne ikke laste eiendomsnavn (databasefeil)."


async def _load_contracts_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle kontrakter – ingen grense, KI Kollega skal lese alle data."""
    try:
        result = await db.execute(text("""
            SELECT c.category, c.status, c.start_date, c.end_date,
                   p.name AS party_name,
                   prop.name AS property_name
            FROM contracts c
            LEFT JOIN parties p ON c.party_id = p.party_id
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties prop ON u.property_id = prop.property_id
            ORDER BY c.end_date ASC NULLS LAST
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen kontrakter i databasen."
        lines = ["Kategori | Status | Start | Utløp | Part | Eiendom"]
        for r in rows:
            cat = (r.category or "-")[:20]
            status = (r.status or "-")[:10]
            start = str(r.start_date) if r.start_date else "-"
            end = str(r.end_date) if r.end_date else "-"
            party = (r.party_name or "-")[:30]
            prop_name = (r.property_name or "-")[:35]
            lines.append(f"{cat} | {status} | {start} | {end} | {party} | {prop_name}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste kontrakter: {e}")
        return "Kunne ikke laste kontraktsdata (databasefeil)."


async def _load_parties_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle parter – ingen grense, KI Kollega skal lese alle data."""
    try:
        result = await db.execute(text("""
            SELECT name, orgnr, contact_email, contact_phone
            FROM parties
            ORDER BY name
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen parter i databasen."
        lines = ["Navn | Orgnr | E-post | Telefon"]
        for r in rows:
            name = (r.name or "-")[:35]
            orgnr = (r.orgnr or "-")[:12]
            email = (r.contact_email or "-")[:30]
            phone = (r.contact_phone or "-")[:15]
            lines.append(f"{name} | {orgnr} | {email} | {phone}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste parter: {e}")
        return "Kunne ikke laste partdata (databasefeil)."


async def _load_units_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle enheter – ingen grense, KI Kollega skal lese alle data."""
    try:
        result = await db.execute(text("""
            SELECT prop.name AS property_name, u.purpose, u.area_sqm, u.floor, u.zone_type
            FROM units u
            JOIN properties prop ON u.property_id = prop.property_id
            ORDER BY prop.name, u.purpose
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen enheter i databasen."
        lines = ["Eiendom | Formål | Areal (m²) | Etasje | Sone"]
        for r in rows:
            prop_name = (r.property_name or "-")[:35]
            purpose = (r.purpose or "-")[:20]
            area = f"{r.area_sqm:.0f}" if r.area_sqm is not None else "-"
            floor = str(r.floor) if r.floor is not None else "-"
            zone = (r.zone_type or "-")[:10]
            lines.append(f"{prop_name} | {purpose} | {area} | {floor} | {zone}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste enheter: {e}")
        return "Kunne ikke laste enhetsdata (databasefeil)."


async def _load_centers_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle sentre – ingen grense, KI Kollega skal lese alle data."""
    try:
        result = await db.execute(text("""
            SELECT name, description, region
            FROM centers
            ORDER BY name
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen sentre i databasen."
        lines = ["Navn | Beskrivelse | Region"]
        for r in rows:
            name = (r.name or "-")[:35]
            desc = (r.description or "-")[:50]
            region = (r.region or "-")[:15]
            lines.append(f"{name} | {desc} | {region}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste sentre: {e}")
        return "Kunne ikke laste senterdata (databasefeil)."


async def _load_property_costs_for_simple_chat(db: AsyncSession) -> str:
    """Hent kostnad per eiendom fra gl_transactions (faktisk regnskap). Fallback til property_husleie_csv og external_data.financials."""
    try:
        # Prioritet: gl_transactions (2024+2025) > property_husleie_csv > external_data.financials
        result = await db.execute(text("""
            SELECT
                p.name,
                p.total_area,
                COALESCE(gl.sum_amount, 0) as total_cost
            FROM properties p
            LEFT JOIN (
                SELECT property_id::text, SUM(belop) as sum_amount
                FROM gl_transactions
                WHERE property_id IS NOT NULL AND ar IN (2024, 2025)
                GROUP BY property_id
            ) gl ON gl.property_id = p.property_id::text
            WHERE p.total_area IS NOT NULL AND p.total_area > 0
            ORDER BY total_cost DESC NULLS LAST
        """))
        rows = result.fetchall()
        # Fallback: hvis ingen GL-data, prøv property_husleie_csv
        if not rows or all((r.total_cost or 0) == 0 for r in rows):
            result2 = await db.execute(text("""
                SELECT
                    p.name,
                    p.total_area,
                    COALESCE(ph.sum_amount, 0) as total_cost
                FROM properties p
                LEFT JOIN (
                    SELECT property_id, SUM(amount) as sum_amount
                    FROM property_husleie_csv
                    WHERE year IN (2024, 2025)
                    GROUP BY property_id
                ) ph ON ph.property_id = p.property_id
                WHERE p.total_area IS NOT NULL AND p.total_area > 0
                ORDER BY total_cost DESC NULLS LAST
            """))
            rows2 = result2.fetchall()
            if rows2 and any((r.total_cost or 0) > 0 for r in rows2):
                rows = rows2
        # Fallback: external_data.financials (legacy)
        if not rows or all((r.total_cost or 0) == 0 for r in rows):
            result3 = await db.execute(text("""
                SELECT
                    p.name,
                    p.total_area,
                    (COALESCE(CAST(NULLIF(TRIM(COALESCE(p.external_data->'financials'->>'total_manual_expenses', '')), '') AS float), 0)
                     + COALESCE(CAST(NULLIF(TRIM(COALESCE(p.external_data->'financials'->>'total_spend_csv', '')), '') AS float), 0)) AS total_cost
                FROM properties p
                WHERE p.total_area IS NOT NULL AND p.total_area > 0
                ORDER BY total_cost DESC NULLS LAST
            """))
            rows3 = result3.fetchall()
            if rows3 and any((r.total_cost or 0) > 0 for r in rows3):
                rows = rows3
        if not rows:
            return "Ingen kostnadsdata per eiendom (sjekk at eiendommer har total_area og at gl_transactions, property_husleie_csv eller external_data.financials er populert)."
        lines = ["Eiendom | Areal (m²) | Totalkostnad (NOK) | Kostnad per kvm (NOK/m²)"]
        for r in rows:
            name = (r.name or "-")[:40]
            area = r.total_area or 0
            total = r.total_cost or 0
            per_kvm = (total / area) if area and area > 0 else 0
            lines.append(f"{name} | {area:.0f} | {total:,.0f} | {per_kvm:,.0f}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste kostnad per eiendom: {e}")
        return "Kunne ikke laste kostnadsdata (databasefeil)."


async def _load_components_for_simple_chat(db: AsyncSession) -> str:
    """Hent alle bygningskomponenter (utstyr) med semantisk data og hierarki."""
    try:
        # Self-join for parent name + Join with Property for context
        result = await db.execute(text("""
            SELECT 
                c.name, 
                c.brick_class, 
                c.system_code,
                p.name as property_name,
                parent.name as parent_name
            FROM building_components c
            JOIN properties p ON c.property_id = p.property_id
            LEFT JOIN building_components parent ON c.parent_id = parent.component_id
            ORDER BY p.name, c.system_code, c.name
            LIMIT 500
        """))
        rows = result.fetchall()
        if not rows:
            return "Ingen bygningskomponenter i databasen."
            
        lines = ["Komponent | Brick/Type | System | Eiendom | Forelder (Tilhører)"]
        for r in rows:
            name = (r.name or "-")[:40]
            brick = (r.brick_class or "-")[:30]
            system = (r.system_code or "-")[:10]
            prop = (r.property_name or "-")[:30]
            parent = (r.parent_name or "-")[:40]
            lines.append(f"{name} | {brick} | {system} | {prop} | {parent}")
            
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple chat: kunne ikke laste komponenter: {e}")
        return "Kunne ikke laste komponentdata (databasefeil)."


def _load_bufdir_familievernkontor_for_simple_chat() -> str:
    """Nasjonal Bufdir-liste (JSON som følger backend-deploy). Tom hvis fil mangler."""
    try:
        from app.services.familievernkontor_bufdir_knowledge import format_compact_catalogue_for_llm

        return format_compact_catalogue_for_llm()
    except Exception as e:
        logger.warning("Simple chat: Bufdir familievernkontor ikke tilgjengelig: %s", e)
        return ""


async def _load_all_domain_data_for_simple_chat(db: AsyncSession) -> str:
    """Hent ALLE domenedata – ingen LIMIT. KI Kollega skal kunne lese alle data."""
    parts = []
    parts.append("=== EIENDOMMER ===")
    parts.append(await _load_properties_for_simple_chat(db))
    parts.append("\n=== EIENDOMMER ALLE NAVN (bruk ved «alle X», «finn alle familievernkontor» etc.) ===")
    parts.append(await _load_all_property_names_for_simple_chat(db))
    parts.append("\n=== KONTRAKTER ===")
    parts.append(await _load_contracts_for_simple_chat(db))
    parts.append("\n=== PARTER (leietakere/leverandører) ===")
    parts.append(await _load_parties_for_simple_chat(db))
    parts.append("\n=== ENHETER (lokaler per eiendom) ===")
    parts.append(await _load_units_for_simple_chat(db))
    parts.append("\n=== SENTRE (kriseentre) ===")
    parts.append(await _load_centers_for_simple_chat(db))
    parts.append("\n=== UTSYR OG KOMPONENTER (FDV, Brick Schema) ===")
    parts.append(await _load_components_for_simple_chat(db))
    parts.append("\n=== KOSTNAD PER EIENDOM (vedlikehold, kostnad per kvm) ===")
    parts.append(await _load_property_costs_for_simple_chat(db))
    bufdir_block = _load_bufdir_familievernkontor_for_simple_chat()
    if bufdir_block:
        parts.append("\n=== BUFDIR / FAMILIEVERNKONTOR (nasjonal oversikt, offisielle navn – supplerer BEFS) ===")
        parts.append(bufdir_block)
    return "\n".join(parts)


router = APIRouter(tags=["KI Kollega"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


# --- Request/Response Schemas ---

class ChatContext(BaseModel):
    """Context information about current page/entity."""
    page: Optional[str] = Field(None, description="Current page path, e.g., /properties/abc-123")
    entity_type: Optional[str] = Field(None, description="Type of entity: property, contract, party")
    entity_id: Optional[str] = Field(None, description="ID of the current entity")
    region: Optional[str] = Field(None, description="Current region filter if any")


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request payload for chat endpoint."""
    message: str = Field(..., description="User's message", min_length=1, max_length=2000)
    context: Optional[ChatContext] = Field(None, description="Current page context")
    conversation_id: Optional[str] = Field(None, description="ID to continue a conversation")
    history: Optional[List[ChatMessage]] = Field(None, description="Previous messages")
    stream: bool = Field(False, description="Whether to stream the response")


_CHAT_PATH_PREFIX_TO_ENTITY = {
    "properties": "property",
    "contracts": "contract",
    "parties": "party",
    "cases": "case",
    "deviations": "deviation",
}
_ENTITY_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def enrich_api_chat_context(ctx: Optional[ChatContext]) -> Optional[ChatContext]:
    """Fyll inn entity_type/entity_id fra ctx.page når klienten kun sender sti (f.eks. /properties/uuid)."""
    if ctx is None:
        return None
    if ctx.entity_type and ctx.entity_id:
        return ctx
    page = (ctx.page or "").split("?")[0].split("#")[0].strip().rstrip("/")
    if not page or page == "/":
        return ctx
    segments = [p for p in page.split("/") if p]
    if len(segments) < 2:
        return ctx
    kind, eid = segments[0], segments[1]
    entity = _CHAT_PATH_PREFIX_TO_ENTITY.get(kind)
    if not entity or not _ENTITY_ID_RE.match(eid):
        return ctx
    return ctx.model_copy(update={"entity_type": entity, "entity_id": eid})


def service_context_from_request(chat_request: ChatRequest):
    """Pydantic ChatContext -> service ChatContext med page-enrich."""
    from app.services.intelligence.ki_kollega.service import ChatContext as ServiceContext

    enriched = enrich_api_chat_context(chat_request.context)
    if not enriched:
        return None
    return ServiceContext(
        page=enriched.page,
        entity_type=enriched.entity_type,
        entity_id=enriched.entity_id,
        region=enriched.region,
    )


class Source(BaseModel):
    """A source referenced in the response."""
    type: str = Field(..., description="Type: property, contract, party, document, web, lovdata")
    id: Optional[str] = Field(None, description="Entity ID if applicable (internal links)")
    name: str = Field(..., description="Display name")
    relevance: float = Field(0.0, description="Relevance score 0-1")
    url: Optional[str] = Field(None, description="External URL for web/lovdata/document links")


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(0, description="Input tokens used")
    completion_tokens: int = Field(0, description="Output tokens used")
    total_tokens: int = Field(0, description="Total tokens used")
    estimated_cost_usd: float = Field(0.0, description="Estimated cost in USD")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    answer: str = Field(..., description="The assistant's answer")
    sources: List[Source] = Field(default_factory=list, description="Referenced sources")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-ups")
    query_type: Optional[str] = Field(None, description="Detected query type")
    conversation_id: str = Field(..., description="Conversation ID for continuity")
    error: Optional[str] = Field(None, description="Error message if any")
    usage: Optional[UsageInfo] = Field(None, description="Token usage information")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data for visualization (e.g. charts)")


# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with KI Kollega.

    Send a message and optionally include:
    - Page context (current property/contract being viewed)
    - Conversation history for multi-turn dialogue

    Returns:
    - AI-generated answer based on BEFS data
    - Sources referenced in the answer
    - Suggested follow-up questions
    """
    context = service_context_from_request(chat_request)

    # Convert history
    history = None
    if chat_request.history:
        history = [{"role": m.role, "content": m.content} for m in chat_request.history]

    # Generate or use conversation ID
    conversation_id = chat_request.conversation_id or str(uuid4())

    # Get response from service
    result = await ki_kollega_service.chat(
        message=chat_request.message,
        context=context,
        history=history,
        db=db,
        user=current_user
    )

    # Map sources to response model
    sources = [
        Source(
            type=s.get("type", "unknown"),
            id=s.get("id"),
            name=s.get("name", "Ukjent"),
            relevance=s.get("relevance", 0.0),
            url=s.get("url")
        )
        for s in result.get("sources", [])
    ]

    # Build usage info if available
    usage_info = None
    usage_data = result.get("usage")
    if usage_data:
        usage_info = UsageInfo(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            estimated_cost_usd=usage_data.get("estimated_cost", 0.0)
        )

    return ChatResponse(
        answer=result.get("answer", "Beklager, jeg kunne ikke generere et svar."),
        sources=sources,
        follow_up_questions=result.get("follow_up_questions", []),
        query_type=result.get("query_type"),
        conversation_id=conversation_id,
        error=result.get("error"),
        usage=usage_info,
        data=result.get("data")
    )


@router.post("/chat/simple", response_model=ChatResponse)
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat_simple(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enkel KI Kollega: én OpenAI-kall med eiendomsdata i konteksten.
    Ingen agent-graf, ingen verktøy – kun data fra DB + brukerens spørsmål.
    Bruk for testing når full flyt er for kompleks.
    """
    conversation_id = chat_request.conversation_id or str(uuid4())

    if not ki_kollega_service.client:
        return ChatResponse(
            answer="Beklager, AI-tjenesten er ikke tilkoblet. Sjekk OPENAI_API_KEY.",
            sources=[],
            follow_up_questions=[],
            conversation_id=conversation_id,
            error="Client not initialized"
        )

    try:
        from app.services.intelligence.ki_kollega.service import get_befs_instruksjoner
        data_text = await _load_all_domain_data_for_simple_chat(db)
        befs_block = get_befs_instruksjoner()
        befs_section = f"\n\n{befs_block}\n\n" if befs_block else "\n\n"
        
        user_info = f"Du snakker med {current_user.name}.\n" if current_user and current_user.name else ""
        system_prompt = f"""Du er KI Kollega, en hjelpsom assistent for BEFS Eiendom.
{user_info}
{befs_section}
Her er ALLE domenedata fra systemet (bruk KUN disse data når du svarer):

{data_text}

Spørsmålstype -> bruk denne tabellen:
- «Alle X», «finn alle familievernkontor», «liste over alle eiendommer med Y i navnet»: bruk EIENDOMMER ALLE NAVN. Filtrer på Navn-kolonnen (f.eks. alle rader der Navn inneholder søkeordet) og list ALLE treff – ikke bare de første. Hvis brukeren sier «alle», vis hele listen. For offisielt navn/telefon til nasjonale familievernkontor (Bufdir), bruk også seksjonen BUFDIR / FAMILIEVERNKONTOR når den finnes.
- Største/minst areal, kvm, eiendommer per by/region, adresse, antall eiendommer: EIENDOMMER.
- Kostnad per kvm, høyest/lavest kostnad per kvm, totalkostnad vedlikehold, sorter på kostnad: KOSTNAD PER EIENDOM. "Billigste eiendom basert på kvm og pris" eller "lavest pris per kvm" = lavest Kostnad per kvm (NOK/m²) – bruk KOSTNAD PER EIENDOM, sorter stigende på Kostnad per kvm.
- Kontrakter utløper, utløpsdato, aktive/terminerte, part per kontrakt, kategori (Leiekontrakt/Serviceavtale): KONTRAKTER.
- Parter/leietakere, orgnr, e-post, telefon, antall parter: PARTER.
- Enheter/lokaler, formål, areal per enhet, etasje, sone (BEBO/ANSA), antall enheter: ENHETER.
- Sentre/kriseentre, region, beskrivelse: SENTRE.
- Utstyr, komponenter, tekniske anlegg: UTSYR OG KOMPONENTER. Se også etter Brick Schema klasser (f.eks. brick:Air_Handler_Unit) og hierarki (hva som tilhører hva).
- Tellinger (hvor mange), oversikt portefølje, nøkkeltall: tell rader i de aktuelle tabellene og oppsummer.
- Sammenligninger: hent relevante rader fra de tabellene som gjelder og sammenlign.

Regler:
- Svar på norsk. Både svare og spørre brukeren tilbake om hva de lurer på.
- For "største eiendom"/"mest kvm": sorter EIENDOMMER på Areal (m²), nevn topp.
- For "høyest kostnad per kvm": sorter KOSTNAD PER EIENDOM på Kostnad per kvm (NOK/m²), nevn topp. For "billigste"/"lavest pris per kvm"/"billigste basert på kvm og pris": samme tabell, sorter lavest Kostnad per kvm først – det er den billigste eiendommen (lavest vedlikeholdskostnad per kvm).
- For "kontrakter utløper snart": bruk KONTRAKTER, kolonnen Utløp.
- Avslutt gjerne med 1–2 oppfølgingsspørsmål. Hvis data mangler, si det kort og spør hva brukeren lurer på."""

        # Build messages with conversation history (cap 10 for token safety)
        openai_messages = [{"role": "system", "content": system_prompt}]
        history = chat_request.history or []
        history_capped = history[-10:]  # last 10 messages (5 turns)
        for m in history_capped:
            role = m.role if m.role in ("user", "assistant") else "user"
            openai_messages.append({"role": role, "content": m.content or ""})
        openai_messages.append({"role": "user", "content": chat_request.message})

        response = await ki_kollega_service.client.chat.completions.create(
            model=ki_kollega_service.model or settings.OPENAI_MODEL,
            messages=openai_messages,
            temperature=0.3,
            max_tokens=1500
        )
        answer = response.choices[0].message.content or "Ingen respons fra modellen."
        return ChatResponse(
            answer=answer,
            sources=[],
            follow_up_questions=[],
            conversation_id=conversation_id,
            usage=UsageInfo(
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0),
                completion_tokens=getattr(response.usage, "completion_tokens", 0),
                total_tokens=getattr(response.usage, "total_tokens", 0),
                estimated_cost_usd=0.0
            ) if getattr(response, "usage", None) else None
        )
    except Exception as e:
        logger.exception("Simple chat failed")
        return ChatResponse(
            answer="Beklager, noe gikk galt. Prøv igjen.",
            sources=[],
            follow_up_questions=[],
            conversation_id=conversation_id,
            error=str(e)[:200]
        )


@router.post("/chat/fullverdig", response_model=ChatResponse)
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat_fullverdig(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fullverdig KI Kollega (AI-first) – Orchestrator + domeneagenter.
    Internkontroll-spørsmål → Internkontroll-agent. Øvrige → Avansert (ki_kollega).
    """
    context = service_context_from_request(chat_request)
    history = [{"role": m.role, "content": m.content} for m in (chat_request.history or [])]
    conversation_id = chat_request.conversation_id or str(uuid4())

    result = await fullverdig_service.chat(
        message=chat_request.message,
        context=context,
        history=history,
        db=db,
        user=current_user
    )

    sources = [
        Source(type=s.get("type", "unknown"), id=s.get("id"), name=s.get("name", "Ukjent"), relevance=s.get("relevance", 0.0), url=s.get("url"))
        for s in result.get("sources", [])
    ]
    usage_data = result.get("usage")
    usage_info = None
    if usage_data:
        usage_info = UsageInfo(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            estimated_cost_usd=usage_data.get("estimated_cost", 0.0)
        )

    return ChatResponse(
        answer=result.get("answer", "Beklager, jeg kunne ikke generere et svar."),
        sources=sources,
        follow_up_questions=result.get("follow_up_questions", []),
        conversation_id=conversation_id,
        error=result.get("error"),
        usage=usage_info
    )


@router.post("/chat/unified", response_model=ChatResponse)
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat_unified(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified KI Kollega (ReAct) – LLM velger verktøy dynamisk.
    Enklere arkitektur enn Avansert; bedre semantisk forståelse.
    """
    context = service_context_from_request(chat_request)
    history = [{"role": m.role, "content": m.content} for m in (chat_request.history or [])]
    conversation_id = chat_request.conversation_id or str(uuid4())

    result = await ki_kollega_service.chat_unified(
        message=chat_request.message,
        context=context,
        history=history,
        db=db,
        user=current_user
    )

    sources = [
        Source(type=s.get("type", "unknown"), id=s.get("id"), name=s.get("name", "Ukjent"), relevance=s.get("relevance", 0.0), url=s.get("url"))
        for s in result.get("sources", [])
    ]

    return ChatResponse(
        answer=result.get("answer", "Beklager, jeg kunne ikke generere et svar."),
        sources=sources,
        follow_up_questions=[],
        conversation_id=conversation_id,
        error=result.get("error"),
        data=result.get("data"),
    )


@router.post("/chat/stream")
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response using Server-Sent Events.
    Yields real LLM tokens as they are generated (Writer node).
    """

    async def generate():
        context = service_context_from_request(chat_request)
        history = [{"role": m.role, "content": m.content} for m in (chat_request.history or [])]
        conversation_id = chat_request.conversation_id or str(uuid4())

        try:
            async for chunk in ki_kollega_service.chat_stream(
                message=chat_request.message,
                context=context,
                history=history,
                db=db,
                user=current_user
            ):
                t = chunk.get("type")
                if t == "status":
                    yield f"data: {json.dumps({'type': 'status', 'content': chunk.get('content', '')})}\n\n"
                elif t == "content":
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.get('content', '')})}\n\n"
                elif t == "done":
                    done_data = {
                        "type": "done",
                        "sources": chunk.get("sources", []),
                        "follow_up_questions": chunk.get("follow_up_questions", []),
                        "conversation_id": conversation_id,
                        "data": chunk.get("data"),
                    }
                    yield f"data: {json.dumps(done_data)}\n\n"
                elif t == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': chunk.get('error', 'Unknown error')})}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)[:200]})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def _pick_suggestions(entity_type: Optional[str], limit: int = 8) -> list:
    """Hent forslag: kontekstbasert (property/contract/party) eller tilfeldig fra 100 eksempelspørsmål."""
    from app.api.v1.ai.suggestions_data import (
        KI_KOLLEGA_EKSEMPELSPORSMAL,
        SUGGESTIONS_BY_ENTITY_TYPE,
    )
    import random

    if entity_type and entity_type in SUGGESTIONS_BY_ENTITY_TYPE:
        pool = SUGGESTIONS_BY_ENTITY_TYPE[entity_type]
        return random.sample(pool, min(limit, len(pool)))
    pool = list(KI_KOLLEGA_EKSEMPELSPORSMAL)
    return random.sample(pool, min(limit, len(pool)))


@router.get("/suggestions")
async def get_suggestions(
    entity_type: Optional[str] = Query(None, description="Current entity type"),
    entity_id: Optional[str] = Query(None, description="Current entity ID"),
    limit: int = Query(8, ge=1, le=20, description="Max number of suggestions"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get contextual question suggestions.

    Returnerer tilfeldig utvalg fra 100+ eksempelspørsmål (eiendommer, kontrakter,
    kostnad, parter, enheter, sentre). Ved entity_type=property/contract/party
    returneres forslag tilpasset den aktuelle siden.
    """
    suggestions = _pick_suggestions(entity_type, limit=limit)
    return {"suggestions": suggestions}


class ProactiveInsight(BaseModel):
    """A proactive insight (warning, info, etc.)."""
    type: str = Field(..., description="Type: warning, info, error")
    content: str = Field(..., description="Markdown content of the insight")


@router.get("/proactive", response_model=List[ProactiveInsight])
async def get_proactive_insights(
    page: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get proactive insights based on current context.
    """
    if not any([page, entity_type, entity_id]):
        return []

    # Construct context
    from app.services.intelligence.ki_kollega.service import ChatContext as ServiceContext
    context = ServiceContext(
        page=page,
        entity_type=entity_type,
        entity_id=entity_id
    )

    try:
        results = await ki_kollega_service.get_proactive_insights(db, context)
        return [
            ProactiveInsight(type=r["type"], content=r["content"])
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error fetching proactive insights: {e}")
        return []



@router.get("/health")
async def health():
    """Check if the AI service is healthy."""
    is_ready = ki_kollega_service.client is not None
    return {
        "status": "healthy" if is_ready else "degraded",
        "client_initialized": is_ready,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/debug")
async def debug_ki_kollega():
    """
    Debug endpoint for KI Kollega - NO AUTH REQUIRED.
    Kun tilgjengelig når ENVIRONMENT != production (f.eks. development).
    """
    from app.core.config import settings
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")

    # Minimal diagnostics in non-prod; no key prefixes (Fix 2 - CODE_REVIEW_30-01)
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "openai_model": settings.OPENAI_MODEL,
        "secret_key_configured": bool(settings.SECRET_KEY),
        "client_initialized": ki_kollega_service.client is not None,
        "environment": settings.ENVIRONMENT,
    }
    
    # Test OpenAI connection
    if ki_kollega_service.client:
        try:
            response = await ki_kollega_service.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": "Si 'OK' på norsk"}],
                max_tokens=10
            )
            diagnostics["openai_test"] = "PASS"
            diagnostics["openai_response"] = response.choices[0].message.content
        except Exception as e:
            diagnostics["openai_test"] = "FAIL"
            diagnostics["openai_error"] = str(e)
    else:
        diagnostics["openai_test"] = "SKIP - client not initialized"
    
    return diagnostics
