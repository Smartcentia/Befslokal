"""
Søk i Bufdir familievernkontor-data (backend/data/familievernkontor_bufdir.json).

Brukes av KI Kollega når brukeren spør om nasjonale familievernkontor (navn, telefon,
region) – supplerer eiendomsregisteret i databasen.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# backend/app/services/ -> backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_JSON = _BACKEND_ROOT / "data" / "familievernkontor_bufdir.json"

_cache: dict[str, Any] | None = None


def _load_data(path: Path | None = None) -> dict[str, Any]:
    global _cache
    p = path or _DEFAULT_JSON
    if _cache is not None and path is None:
        return _cache
    if not p.exists():
        logger.warning("familievernkontor_bufdir.json ikke funnet: %s", p)
        empty = {"offices": [], "_missing_file": str(p)}
        if path is None:
            _cache = empty
        return empty
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if path is None:
            _cache = data
        return data
    except Exception as e:
        logger.error("Kunne ikke lese familievernkontor_bufdir.json: %s", e)
        return {"offices": []}


def clear_cache() -> None:
    """For tester."""
    global _cache
    _cache = None


def _haystack(office: dict[str, Any]) -> str:
    parts = [
        office.get("slug") or "",
        office.get("official_name") or "",
        office.get("region") or "",
        office.get("list_page_link_text") or "",
        office.get("document_title") or "",
        " ".join(office.get("phones") or []),
        " ".join(office.get("emails") or []),
    ]
    for sec in office.get("accordion_sections") or []:
        if sec.get("title") == "Kontakt og timebestilling":
            parts.append(sec.get("text") or "")
            break
    return " ".join(parts).lower()


def _score(office: dict[str, Any], query: str) -> float:
    q = (query or "").strip().lower()
    if len(q) < 2:
        return 0.0
    hay = _haystack(office)
    if not hay:
        return 0.0
    score = 0.0
    if q in hay:
        score += 50.0
    for w in re.findall(r"[a-zæøå0-9]+", q):
        if len(w) < 3:
            continue
        if w in hay:
            score += float(hay.count(w))
    slug = (office.get("slug") or "").replace("-", " ")
    if slug and slug in q.replace("-", " "):
        score += 15.0
    return score


def search_bufdir_familievernkontor(
    search_term: str,
    *,
    limit: int = 8,
    json_path: Path | None = None,
) -> str:
    """
    Returnerer formatert tekst for LLM. Tom streng hvis ingen treff eller manglende fil.
    """
    data = _load_data(json_path)
    offices = list(data.get("offices") or [])
    if not offices:
        return ""

    scored: list[tuple[float, dict[str, Any]]] = []
    for o in offices:
        s = _score(o, search_term)
        if s > 0:
            scored.append((s, o))
    scored.sort(key=lambda x: -x[0])
    top = [o for _, o in scored[:limit]]

    if not top:
        q = (search_term or "").strip().lower()
        if len(q) >= 2:
            for o in offices:
                if q in _haystack(o):
                    top.append(o)
                    if len(top) >= limit:
                        break

    if not top:
        return ""

    lines: list[str] = [
        "Kilde: Bufdir.no (familievernkontor), synkronisert datasett i BEFS.",
        "",
    ]
    for o in top:
        name = o.get("official_name") or o.get("slug") or "?"
        region = o.get("region") or ""
        url = o.get("url") or ""
        phones = ", ".join(o.get("phones") or []) or "-"
        emails = ", ".join(o.get("emails") or []) or "-"
        contact = ""
        for sec in o.get("accordion_sections") or []:
            if sec.get("title") == "Kontakt og timebestilling":
                contact = (sec.get("text") or "")[:900]
                break
        lines.append(f"• {name} ({region})")
        lines.append(f"  Nettside: {url}")
        lines.append(f"  Telefon: {phones} | E-post: {emails}")
        if contact:
            lines.append(f"  Kontakt/timebestilling (utdrag): {contact.replace(chr(10), ' ')[:700]}")
        lines.append("")
    return "\n".join(lines).strip()


def format_office_one_line(office: dict[str, Any]) -> str:
    """Kort linje for opplisting."""
    n = office.get("official_name") or office.get("slug")
    r = office.get("region") or ""
    return f"{n} | {r}"


def format_compact_catalogue_for_llm(max_chars: int = 14000) -> str:
    """
    Alle kontorer som tabell (for enkel chat uten verktøy).
    Avkortes hvis for lang for kontekstvindu.
    """
    data = _load_data()
    offices = list(data.get("offices") or [])
    if not offices:
        return ""
    rows = []
    for o in sorted(
        offices,
        key=lambda x: ((x.get("region") or ""), (x.get("official_name") or x.get("slug") or "")),
    ):
        name = (o.get("official_name") or o.get("slug") or "-")[:70]
        region = (o.get("region") or "-")[:24]
        ph = (", ".join(o.get("phones") or []) or "-")[:28]
        url = (o.get("url") or "")[:80]
        rows.append(f"{name} | {region} | {ph} | {url}")
    header = "Navn (Bufdir) | Region | Telefon | Lenke"
    lines = [
        "=== BUFDIR.NO – FAMILIEVERNKONTOR (nasjonal oversikt, offisielle navn) ===",
        "Dette er ikke nødvendigvis lik eiendomslisten i BEFS; bruk for spørsmål om telefon, kontor, region.",
        header,
        *rows,
    ]
    text = "\n".join(lines)
    if len(text) > max_chars:
        return text[: max_chars - 40] + "\n[... avkortet for token-grense ...]"
    return text
