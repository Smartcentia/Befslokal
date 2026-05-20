"""
Barnevern fagkunnskap – søk og oppslag i backend/data/barnevern_fagkunnskap.json.

Brukes av KI Kollega når brukeren spør om:
- Roller og ansvar i institusjonsbarnevernet
- Kommunal egenandel / satser / 2026-sjokket
- Tekniske krav til barnevernsinstitusjoner (RKL 6, TEK17, NS 8175)
- Kvalitetsindikatorer og styringssignaler
- Ettervern og internkontrollkrav
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_JSON = _BACKEND_ROOT / "data" / "barnevern_fagkunnskap.json"

_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    if not _DEFAULT_JSON.exists():
        logger.warning("barnevern_fagkunnskap.json ikke funnet: %s", _DEFAULT_JSON)
        _cache = {}
        return _cache
    try:
        with open(_DEFAULT_JSON, encoding="utf-8") as f:
            _cache = json.load(f)
        return _cache
    except Exception as e:
        logger.error("Kunne ikke lese barnevern_fagkunnskap.json: %s", e)
        _cache = {}
        return _cache


def clear_cache() -> None:
    global _cache
    _cache = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_egenandel_satser() -> str:
    """Returnerer kommunale egenandel-satser som formatert tekst for LLM."""
    data = _load()
    eg = data.get("kommunal_egenandel", {})
    if not eg:
        return ""

    lines = [
        "Kommunal egenandel til statlige barnevernstiltak (barnevernsloven § 16-5):",
        "",
        f"{'Tiltakskategori':<45} {'2024':>12} {'2025':>12} {'2026':>12}",
        "-" * 83,
    ]
    for s in eg.get("satser", []):
        lines.append(
            f"{s['kategori']:<45} {s['sats_2024']:>12,.0f} {s['sats_2025']:>12,.0f} {s['sats_2026']:>12,.0f} kr/mnd"
        )

    varsel = eg.get("varsel_2026", {})
    if varsel:
        lines += [
            "",
            f"⚠️  {varsel['tittel']}",
            f"Fra {varsel['ikrafttredelse']}: Egenandel øker fra kr {varsel['gammel_sats']:,} "
            f"til kr {varsel['ny_sats']:,} per måned ({varsel['økning_pct']} % økning).",
            "Gjelder spesialiserte fosterhjem inngått FØR 2022.",
        ]

    return "\n".join(lines)


def get_roller_og_ansvar() -> str:
    """Returnerer roller/ansvar-oversikt som formatert tekst for LLM."""
    data = _load()
    roa = data.get("roller_og_ansvar", {})
    if not roa:
        return ""

    lines = [roa.get("title", "Roller og ansvar i institusjonsbarnevernet"), ""]
    for a in roa.get("aktorer", []):
        lines.append(f"**{a['navn']}** – {a['rolle']}")
        for punkt in a.get("ansvar", []):
            lines.append(f"  • {punkt}")
        lines.append("")
    return "\n".join(lines).strip()


def get_kvalitetsindikatorer() -> str:
    """Returnerer kvalitetsindikatorer og styringssignaler som tekst for LLM."""
    data = _load()
    ki = data.get("kvalitetsindikatorer", {})
    if not ki:
        return ""

    lines = [ki.get("title", "Kvalitetsindikatorer"), ""]
    for omr in ki.get("omrader", []):
        lines.append(f"• **{omr['indikator']}**: {omr['beskrivelse']} (kilde: {omr['kilde']})")
    lines += ["", "Styringssignaler 2025:"]
    for sg in ki.get("styringssignaler_2025", []):
        lines.append(f"  – {sg}")
    return "\n".join(lines)


def get_tekniske_krav() -> str:
    """Returnerer tekniske krav til barnevernsinstitusjoner som tekst for LLM."""
    data = _load()
    tk = data.get("tekniske_krav_institusjon", {})
    if not tk:
        return ""

    lines = [tk.get("title", "Tekniske krav"), ""]

    rk = tk.get("risikoklasse", {})
    lines.append(f"Risikoklasse: **{rk.get('klasse', 'RKL 6')}** – {rk.get('begrunnelse', '')}")
    lines.append("Krav:")
    for k in rk.get("krav", []):
        lines.append(f"  • {k}")

    lyd = tk.get("lydkrav", {})
    lines += [
        "",
        f"Lydkrav (NS 8175): minimum {lyd.get('minimumskrav', 'lydklasse C')}, "
        f"anbefalt {lyd.get('anbefalt', 'B')}. "
        f"Luftlydisolasjon Rw {lyd.get('luftlydisolasjon_rw_db', '≥55 dB')}.",
    ]

    sank = data.get("internkontroll_og_sanksjoner", {}).get("sanksjoner", {})
    if sank:
        lines += [
            "",
            f"Sanksjonsrisiko: Mangelfull internkontroll kan gi gebyr inntil "
            f"kr {sank.get('maksimalt_gebyr_kr', 9_000_000):,}.",
        ]

    return "\n".join(lines)


def search_barnevern_kunnskap(query: str) -> str:
    """
    Søk i alle seksjoner av barnevern fagkunnskap.
    Returnerer formatert tekst for LLM basert på relevante nøkkelord.
    """
    q = (query or "").lower()
    parts: list[str] = []

    if any(w in q for w in ("egenandel", "sats", "månedlig", "kommunal", "betaling", "2026", "sjokk",
                             "fosterhjem", "mst", "multisystemisk", "senter for foreldre")):
        t = get_egenandel_satser()
        if t:
            parts.append("### Kommunal egenandel\n" + t)

    if any(w in q for w in ("rolle", "ansvar", "bufdir", "bufetat", "bfd", "statsforvalter",
                             "nemnda", "helsetilsyn", "kommune", "hvem", "organisering")):
        t = get_roller_og_ansvar()
        if t:
            parts.append("### Roller og ansvar\n" + t)

    if any(w in q for w in ("styringssignal", "kvalitet", "indikator", "stabilitet", "trygghet",
                             "skolegang", "medvirkning", "ettervern", "behandlings", "tilbud")):
        t = get_kvalitetsindikatorer()
        if t:
            parts.append("### Kvalitetsindikatorer og styringssignaler\n" + t)

    if any(w in q for w in ("teknisk", "krav", "brann", "rkl", "risikoklasse", "sprinkler",
                             "lyd", "ns 8175", "tek17", "arkitektur", "tid", "traumesensitiv",
                             "rom", "soverom", "bad", "sikkerhet", "hms", "material")):
        t = get_tekniske_krav()
        if t:
            parts.append("### Tekniske krav til barnevernsinstitusjoner\n" + t)

    # Fallback: hvis ingen keywords matchet men spørsmålet er om barnevern generelt
    if not parts and any(w in q for w in ("institusjon", "barnevern", "barn", "bufetat", "bufdir")):
        parts = [
            "### Kommunal egenandel\n" + get_egenandel_satser(),
            "### Roller og ansvar\n" + get_roller_og_ansvar(),
        ]

    if not parts:
        return ""

    header = "Kilde: Barnevern fagkunnskap (BEFS intern referansedatabase, 2025–2026).\n\n"
    return header + "\n\n".join(p for p in parts if p.strip())
