"""
Commercial Due Diligence (DD) / risikovurdering for leietakere.

Kjører målrettede websøk (konkurs, rettssak, svindel, erfaringer, regnskapstall, daglig leder),
sender resultater + BRREG-data til LLM, returnerer strukturert JSON for trafikklys og røde flagg.

Brukes av: POST /parties/{party_id}/due-diligence
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.mcp.handler import search_web_tool

logger = logging.getLogger(__name__)

REASON_NO_KEY = "OPENAI_API_KEY er ikke satt på serveren. Legg den til under Environment i Railway Dashboard."
REASON_NO_WEB_RESULTS = "Web-søk ga ingen treff. Prøv igjen senere."
REASON_OPENAI_ERROR = "OpenAI API feilet. Sjekk at du har saldo på kontoen (quota) eller rett API-nøkkel i Railway. (Tips: Sjekk platform.openai.com/usage)"

# Søkequeries for DD (suffiks per plan)
DD_SEARCH_QUERIES = [
    ("konkurs", "Konkursfare, konkursbegjæring"),
    ("rettssak", "Rettssaker, tvister, dommer"),
    ("svindel", "Svindel, kriminalitet"),
    ("erfaringer", "Kunde-/leverandøranmeldelser"),
    ("regnskapstall", "Økonomiske trender (Proff, Purehelp)"),
    ("daglig leder", "Nøkkelpersoner, tidligere konkurser"),
]

DD_SYSTEM_PROMPT = """# ROLLE
Du er en ekspert på risikoanalyse og "Commercial Due Diligence" for eiendom. Din oppgave er å analysere søkeresultater for en spesifikk organisasjon for å avdekke potensielle risikoer ved et leieforhold.

# KONTEKST
Vi vurderer å inngå (eller fornye) en leiekontrakt med denne organisasjonen. Vi trenger å vite om de er betalingsdyktige, pålitelige og om de utgjør en omdømmemessig eller juridisk risiko.

# ANALYSEOMRÅDER
Gå gjennom den tildelte informasjonen/søkeresultatene og evaluer risiko basert på følgende kategorier:

1. **Finansiell Risiko:**
   - Tegn på konkursfare, betalingsanmerkninger, eller store underskudd nylig.
   - Negativ utvikling i omsetning eller resultat (hvis tilgjengelig i utdragene).

2. **Juridisk & Regulatorisk Risiko:**
   - Pågående eller tidligere rettssaker, tvister eller dommer.
   - Bøter, sanksjoner eller problemer med myndigheter (f.eks. Arbeidstilsynet).

3. **Omdømmerisiko:**
   - Negativ medieomtale, skandaler eller kontroverser.
   - Koblinger til uetisk drift, hvitvasking eller kriminalitet.
   - Ekstremt dårlige anmeldelser/erfaringer fra kunder eller tidligere utleiere.

4. **Operasjonell Risiko:**
   - Hyppige skifter i ledelsen.
   - Ustabil bransje.

# VIKTIGE REGLER
- **Vær kildekritisk:** Skille mellom rykter i sosiale medier og faktiske nyhetsartikler eller rettsdokumenter.
- **Ingen "Hallucinering":** Hvis du ikke finner informasjon om risiko, skriv "Ingen informasjon funnet". Ikke finn på data.
- **Sitering:** Referer alltid til kilden (URL eller nettsted) der du fant informasjonen.

# OUTPUT FORMAT
Returner KUN gyldig JSON. Ingen markdown, ingen forklaring utenfor JSON. Bruk nøyaktig denne strukturen:

{
  "risk_level": "LAV" | "MIDDELS" | "HØY",
  "summary": "Kort begrunnelse på 2 setninger.",
  "red_flags": ["Punkt 1", "Punkt 2"],
  "detailed_analysis": {
    "okonomi": "Dine funn...",
    "juridisk": "Dine funn...",
    "omdømme": "Dine funn..."
  },
  "follow_up_questions": ["Spørsmål 1", "Spørsmål 2"],
  "sources": [
    {"url": "https://...", "title": "..."}
  ]
}

Hvis ingen røde flagg: "red_flags": []
Hvis ingen oppfølgingsspørsmål: "follow_up_questions": []
"""


def _format_brreg_context(brreg_data: Optional[Dict[str, Any]]) -> str:
    """Formater BRREG-data som kontekststreng til LLM. brreg_data kan inneholde brreg_enhet-felter og evt. brreg_roller."""
    if not brreg_data or not isinstance(brreg_data, dict):
        return ""
    lines = ["## BRREG-data (Brønnøysundregistrene):"]
    if brreg_data.get("konkurs"):
        lines.append(f"- Konkurs: {brreg_data.get('konkurs')} (dato: {brreg_data.get('konkursdato', 'N/A')})")
    if brreg_data.get("underAvvikling"):
        lines.append(f"- Under avvikling: {brreg_data.get('underAvvikling')}")
    if brreg_data.get("underTvangsavviklingEllerTvangsopplosning"):
        lines.append("- Under tvangsavvikling eller tvangsoppløsning")
    if brreg_data.get("stiftelsesdato"):
        lines.append(f"- Stiftelsesdato: {brreg_data.get('stiftelsesdato')}")
    if brreg_data.get("naeringskode1"):
        n = brreg_data["naeringskode1"]
        if isinstance(n, dict):
            lines.append(f"- Næring: {n.get('beskrivelse') or n.get('kode') or 'N/A'}")
    roller_list = None
    brreg_roller = brreg_data.get("brreg_roller")
    if isinstance(brreg_roller, dict) and brreg_roller.get("roller"):
        roller_list = brreg_roller["roller"]
    if roller_list:
        for r in roller_list[:5]:
            role = "?"
            if isinstance(r.get("type"), dict):
                role = r["type"].get("beskrivelse", "?")
            person = ""
            if isinstance(r.get("person"), dict) and isinstance(r["person"].get("navn"), dict):
                n = r["person"]["navn"]
                person = f"{n.get('fornavn', '')} {n.get('etternavn', '')}".strip()
            if person:
                lines.append(f"- {role}: {person}")
    if len(lines) <= 1:
        return ""
    return "\n".join(lines)


def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedupliser søkeresultater på URL."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for r in results:
        url = (r.get("href") or r.get("url") or "").strip()
        if url and url not in seen:
            seen.add(url)
            out.append(r)
    return out


async def run_due_diligence(
    company_name: str,
    orgnr: str,
    brreg_data: Optional[Dict[str, Any]] = None,
    *,
    return_reason: bool = False,
) -> Dict[str, Any] | tuple[Dict[str, Any] | None, Optional[str]]:
    """
    Kjør Due Diligence: multi-query websøk + LLM-analyse.

    Args:
        company_name: Firmanavn
        orgnr: Organisasjonsnummer (9 siffer)
        brreg_data: Valgfri brreg_enhet fra party.external_data
        return_reason: Ved True returneres (None, reason) ved feil

    Returns:
        Dict med risk_level, summary, red_flags, detailed_analysis, follow_up_questions, sources.
        Ved return_reason=True og feil: (None, reason).
    """
    name = (company_name or "").strip()
    nr = (orgnr or "").replace(" ", "").strip()
    if not name or len(nr) != 9 or not nr.isdigit():
        if return_reason:
            return (None, "Ugyldig firmanavn eller orgnr.")
        return {
            "risk_level": "MIDDELS",
            "summary": "Kunne ikke kjøre vurdering: ugyldig input.",
            "red_flags": [],
            "detailed_analysis": {"okonomi": "", "juridisk": "", "omdømme": ""},
            "follow_up_questions": [],
            "sources": [],
        }

    if not getattr(settings, "OPENAI_API_KEY", None) or not (settings.OPENAI_API_KEY or "").strip():
        if return_reason:
            return (None, REASON_NO_KEY)
        return {
            "risk_level": "MIDDELS",
            "summary": REASON_NO_KEY,
            "red_flags": [],
            "detailed_analysis": {"okonomi": "", "juridisk": "", "omdømme": ""},
            "follow_up_questions": [],
            "sources": [],
        }

    # 1. Kjør alle søk
    all_results: List[Dict[str, Any]] = []
    for suffix, _ in DD_SEARCH_QUERIES:
        query = f'"{name}" {suffix}'
        try:
            hits = await search_web_tool(query, max_results=5)
            if isinstance(hits, list):
                all_results.extend(hits)
        except Exception as e:
            logger.warning(f"DD search failed for '{query}': {e}")

    all_results = _deduplicate_results(all_results)
    if not all_results:
        if return_reason:
            return (None, REASON_NO_WEB_RESULTS)
        return {
            "risk_level": "MIDDELS",
            "summary": REASON_NO_WEB_RESULTS,
            "red_flags": [],
            "detailed_analysis": {"okonomi": "", "juridisk": "", "omdømme": ""},
            "follow_up_questions": [],
            "sources": [],
        }

    # 2. Bygg kontekst
    snippets = "\n\n".join(
        f"[{r.get('title', '')}]({r.get('href', '')})\n{(r.get('body') or '')[:500]}"
        for r in all_results[:30]
    )
    brreg_ctx = _format_brreg_context(brreg_data)
    virksomhet_url = f"https://virksomhet.brreg.no/nb/oppslag/enheter/{nr}"
    user_content = f"Organisasjon: {name}, orgnr {nr}.\n\n"
    if brreg_ctx:
        user_content += brreg_ctx + "\n\n"
    user_content += "## Websøkeresultater:\n\n" + snippets[:14000]
    user_content += f"\n\nOffisiell kilde: {virksomhet_url}"

    # 3. LLM-kall
    try:
        from app.core.ai_utils import get_ai_client
        client, model = get_ai_client()

        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": DD_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            if return_reason:
                return (None, REASON_OPENAI_ERROR)
            return {
                "risk_level": "MIDDELS",
                "summary": "LLM returnerte tomt svar.",
                "red_flags": [],
                "detailed_analysis": {"okonomi": "", "juridisk": "", "omdømme": ""},
                "follow_up_questions": [],
                "sources": [],
            }

        data = json.loads(raw)
        # Normaliser felt
        if "risk_level" not in data:
            data["risk_level"] = "MIDDELS"
        if "red_flags" not in data:
            data["red_flags"] = []
        if "detailed_analysis" not in data:
            data["detailed_analysis"] = {"okonomi": "", "juridisk": "", "omdømme": ""}
        if "follow_up_questions" not in data:
            data["follow_up_questions"] = []
        if "sources" not in data:
            data["sources"] = []

        # Legg til virksomhet.brreg.no som kilde
        if not any(s.get("url", "").find("virksomhet.brreg.no") >= 0 for s in data.get("sources", [])):
            data.setdefault("sources", []).append({
                "url": virksomhet_url,
                "title": "Brønnøysundregistrene – Virksomhetsopplysninger",
            })

        if return_reason:
            return (data, None)
        return data

    except json.JSONDecodeError as e:
        logger.warning(f"DD LLM returned invalid JSON: {e}")
        if return_reason:
            return (None, f"{REASON_OPENAI_ERROR} Ugyldig JSON.")
        return {
            "risk_level": "MIDDELS",
            "summary": "Kunne ikke parse LLM-svar.",
            "red_flags": [],
            "detailed_analysis": {"okonomi": "", "juridisk": "", "omdømme": ""},
            "follow_up_questions": [],
            "sources": [],
        }
    except Exception as e:
        logger.exception(f"DD OpenAI error: {e}")
        if return_reason:
            return (None, f"{REASON_OPENAI_ERROR} Feil: {e!s}")
        return {
            "risk_level": "MIDDELS",
            "summary": str(e),
            "red_flags": [],
            "detailed_analysis": {"okonomi": "", "juridisk": "", "omdømme": ""},
            "follow_up_questions": [],
            "sources": [],
        }
