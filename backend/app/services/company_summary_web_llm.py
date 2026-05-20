"""
Firmaoppsummering via internett-søk (DuckDuckGo) + LLM (OpenAI).

Brukes av:
- Script: enrich_parties_openai_company.py (batch)
- API: POST /parties/{party_id}/company-summary-from-web (on-demand)

Gir samme type detaljert oppsummering som man får fra f.eks. Gemini:
Company Overview, Key Roles, Financial Snapshot, Corporate Structure.
"""
from __future__ import annotations

from typing import Optional, Tuple, Dict, Any

from app.core.config import settings
from app.services.mcp.handler import search_web_tool

# Feilårsaker for tydelig API-svar
REASON_NO_KEY = "OPENAI_API_KEY er ikke satt på serveren. Legg den til under Environment i Railway Dashboard."
REASON_NO_WEB_RESULTS = "Web-søk ga ingen treff. Prøv igjen senere."
REASON_OPENAI_ERROR = "OpenAI API feilet. Sjekk at du har saldo på kontoen (quota) eller rett API-nøkkel i Railway. (Tips: Sjekk platform.openai.com/usage)"


COMPANY_SUMMARY_SYSTEM_PROMPT = """You are an assistant that creates structured company summaries based on web search results.
Given search results for a Norwegian company (name and organization number), produce a clear summary. Use these sections when information is available:

**Company Overview**
- Company Name, Organization Number (with spaces: XXX XXX XXX)
- Incorporation Date (stiftelsesdato)
- Business Address, Municipality
- Industry (NACE code and description)

**Key Roles & Management**
- General Manager (Daglig leder)
- Chair of the Board (Styreleder)
- Deputy Board Member, Auditor (revisor)
- Ownership (eierforhold)

**Financial Snapshot** (if mentioned – e.g. latest year)
- Operating Revenue (driftsinntekt)
- Operating Profit/Loss (driftsresultat)
- Equity (egenkapital)
- Share Capital (aksjekapital)

**Corporate Structure & Holdings**
- Subsidiaries, associated companies, or related entities (datterselskap / tilknyttede selskaper)

Write in English or Norwegian as fits the source material. Be concise but include all details found; do not invent data. If a section has no information in the search results, omit it. End with a blank line."""


BRREG_ONLY_SYSTEM_PROMPT = """You are an assistant that creates structured company summaries based on BRREG (Brønnøysundregistrene) data.
Given the BRREG data for a Norwegian company, produce a clear summary. Use these sections when information is available:

**Company Overview**
- Company Name, Organization Number (with spaces: XXX XXX XXX)
- Incorporation Date (stiftelsesdato)
- Business Address, Municipality
- Industry (NACE code and description)

**Key Roles & Management**
- General Manager (Daglig leder)
- Chair of the Board (Styreleder)
- Deputy Board Member, Auditor (revisor)

Only include information that is explicitly in the data. Do not invent data. Write in Norwegian."""


def _format_brreg_for_summary(brreg_data: Dict[str, Any]) -> str:
    """Formater BRREG-data som kontekst til LLM. Støtter både rå BRREG-format og extended (name/orgNr)."""
    if not brreg_data or not isinstance(brreg_data, dict):
        return ""
    lines = []
    name = brreg_data.get("navn") or brreg_data.get("name")
    if name:
        lines.append(f"Navn: {name}")
    nr = brreg_data.get("organisasjonsnummer") or brreg_data.get("orgNr") or brreg_data.get("id")
    if nr:
        lines.append(f"Org.nr: {nr}")
    if brreg_data.get("stiftelsesdato"):
        lines.append(f"Stiftelsesdato: {brreg_data['stiftelsesdato']}")
    of = brreg_data.get("organisasjonsform")
    if isinstance(of, dict):
        lines.append(f"Organisasjonsform: {of.get('beskrivelse', of.get('kode', ''))}")
    elif brreg_data.get("organisasjonsform_beskrivelse"):
        lines.append(f"Organisasjonsform: {brreg_data['organisasjonsform_beskrivelse']}")
    n = brreg_data.get("naeringskode1")
    if isinstance(n, dict):
        lines.append(f"Næring: {n.get('beskrivelse', n.get('kode', ''))}")
    if brreg_data.get("address"):
        lines.append(f"Adresse: {brreg_data['address']}")
    for addr_key in ("forretningsadresse", "postadresse"):
        addr = brreg_data.get(addr_key)
        if isinstance(addr, dict):
            adr = addr.get("adresse", [])
            if isinstance(adr, list):
                parts = [str(p) for p in adr if p]
            else:
                parts = []
            poststed = addr.get("poststed", "")
            if poststed:
                parts.append(poststed)
            if parts:
                lines.append(f"{addr_key}: {', '.join(parts)}")
    brreg_roller = brreg_data.get("brreg_roller")
    if isinstance(brreg_roller, dict) and brreg_roller.get("roller"):
        lines.append("Roller:")
        for r in brreg_roller["roller"][:8]:
            role = "?"
            if isinstance(r.get("type"), dict):
                role = r["type"].get("beskrivelse", "?")
            person = ""
            if isinstance(r.get("person"), dict) and isinstance(r["person"].get("navn"), dict):
                n = r["person"]["navn"]
                person = f"{n.get('fornavn', '')} {n.get('etternavn', '')}".strip()
            if person:
                lines.append(f"  - {role}: {person}")
    return "\n".join(lines) if lines else ""


async def _call_openai_for_summary(
    name: str,
    nr: str,
    user_content: str,
    system_prompt: str,
    *,
    return_reason: bool,
) -> Optional[str] | Tuple[Optional[str], Optional[str]]:
    """Kall OpenAI for å generere oppsummering."""
    try:
        from app.core.ai_utils import get_ai_client
        client, model = get_ai_client()
        
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content[:12000]},
            ],
            max_tokens=1024,
        )
        text = (resp.choices[0].message.content or "").strip()
        if return_reason:
            return (text if text else None, None if text else REASON_OPENAI_ERROR)
        return text if text else None
    except Exception as e:
        if return_reason:
            return (None, f"{REASON_OPENAI_ERROR} Feil: {e!s}")
        return None


async def fetch_company_summary_via_web_llm(
    company_name: str,
    orgnr: str,
    *,
    max_search_results: int = 5,
    return_reason: bool = False,
    brreg_data: Optional[Dict[str, Any]] = None,
) -> Optional[str] | Tuple[Optional[str], Optional[str]]:
    """
    Søk på nettet (DuckDuckGo) etter firma + orgnr, send snippeter til OpenAI,
    returner firmaoppsummering som tekst (eller None ved feil).

    Hvis websøk feiler men brreg_data er tilgjengelig: bruk Brreg-data som fallback.
    Hvis return_reason=True: returnerer (summary, None) ved suksess eller (None, reason) ved feil.
    Krever OPENAI_API_KEY. Bruker search_web_tool (DuckDuckGo, ingen ekstra nøkkel).
    """
    name = (company_name or "").strip()
    nr = (orgnr or "").replace(" ", "").strip()
    if not name or len(nr) != 9 or not nr.isdigit():
        return (None, "Ugyldig firmanavn eller orgnr.") if return_reason else None

    if not getattr(settings, "OPENAI_API_KEY", None) or not (settings.OPENAI_API_KEY or "").strip():
        return (None, REASON_NO_KEY) if return_reason else None

    query = f"{name} {nr} Norge"
    try:
        results = await search_web_tool(query, max_results=max_search_results)
    except Exception as e:
        if brreg_data:
            return await _fallback_brreg_summary(name, nr, brreg_data, return_reason)
        return (None, f"Web-søk feilet: {e!s}") if return_reason else None

    if isinstance(results, list) and results:
        snippets = "\n\n".join(
            f"[{r.get('title', '')}]({r.get('href', '')})\n{(r.get('body') or '')[:500]}"
            for r in results[:max_search_results]
        )
        user_content = f"Company: {name}, organization number {nr}.\n\nWeb search results:\n{snippets}"
        return await _call_openai_for_summary(
            name, nr, user_content, COMPANY_SUMMARY_SYSTEM_PROMPT, return_reason=return_reason
        )

    # Websøk ga ingen treff – prøv fallback med Brreg
    if brreg_data:
        return await _fallback_brreg_summary(name, nr, brreg_data, return_reason)
    return (None, REASON_NO_WEB_RESULTS) if return_reason else None


async def _fallback_brreg_summary(
    name: str,
    nr: str,
    brreg_data: Dict[str, Any],
    return_reason: bool,
) -> Optional[str] | Tuple[Optional[str], Optional[str]]:
    """Fallback: generer oppsummering fra Brreg-data når websøk feiler."""
    ctx = _format_brreg_for_summary(brreg_data)
    if not ctx.strip():
        return (None, REASON_NO_WEB_RESULTS) if return_reason else None
    user_content = f"Company: {name}, organization number {nr}.\n\nBRREG data:\n{ctx}"
    return await _call_openai_for_summary(
        name, nr, user_content, BRREG_ONLY_SYSTEM_PROMPT, return_reason=return_reason
    )
