"""
Bygg adresse→navn-mapping fra backend/data/familievernkontor_bufdir.json
(generert av scrape_familievernkontor_bufdir.py).

Brukes av berik_navn_familievernkontor.py sammen med manuelle oppføringer
i familievernkontor_mapping.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Norsk postnr + stedsnavn (unngår treff i klokkeslett 08:30-15:00)
_POSTAL_LINE = re.compile(
    r"([A-Za-z0-9ÆØÅæøå'—][A-Za-z0-9ÆØÅæøå'—\s\.\-]+?)"
    r",\s*(\d{4})\s+"
    r"([A-Za-zÆØÅæøå][A-Za-zÆØÅæøåa-zæøå\s\-]+)"
)

# Gate/adresse uten postnr men med komma før stedsnavn (f.eks. «…, Arendal»)
_CITY_ONLY = re.compile(
    r"^(?:[^:]+:\s*)?"
    r"(.+?),\s*"
    r"([A-Za-zÆØÅæøå][a-zæøå]+(?:\s+[A-Za-zÆØÅæøå][a-zæøå]+)?)\s*$"
)

_SKIP_SUBSTR = (
    "telefon",
    "e-post",
    "postboks",
    "kommunene",
    "dekker",
    "mekling",
    "bestill",
    "åpning",
    "kl.",
    "uke ",
)


def _preprocess_contact_block(text: str) -> str:
    t = text.replace("\r", "")
    t = re.sub(r"(?im)^Adresse\s*\n\s*:\s*", "Adresse: ", t)
    t = re.sub(
        r"(?im)^Post-\s*og\s*besøksadresse\s*\n\s*:\s*",
        "Post- og besøksadresse: ",
        t,
    )
    t = re.sub(r"(?im)^Besøksadresse\s*\n\s*:\s*", "Besøksadresse: ", t)
    t = re.sub(r"(?im)^Postadresse\s*\n\s*:\s*", "Postadresse: ", t)
    return t


def _shorten_street(street: str) -> str:
    street = street.strip()
    parts = [p.strip() for p in street.split(",")]
    if len(parts) >= 2 and re.match(r"^\d+\.?\s*etasje", parts[-1], re.I):
        return ", ".join(parts[:-1]).strip()
    return street


def _contact_section(office: dict[str, Any]) -> str:
    for sec in office.get("accordion_sections") or []:
        if sec.get("title") == "Kontakt og timebestilling":
            return sec.get("text") or ""
    return ""


def _bad_context(s: str) -> bool:
    sl = s.lower()
    return any(x in sl for x in _SKIP_SUBSTR)


def extract_auto_mappings_from_office(office: dict[str, Any]) -> list[dict[str, Any]]:
    """Returnerer lister med address_pattern, postal (kan være tom), name, source."""
    name = (office.get("official_name") or "").strip()
    if not name:
        return []

    text = _preprocess_contact_block(_contact_section(office))
    if not text:
        return []

    out: list[dict[str, Any]] = []

    # Én linje for regex på hele blokken (fanger sammenhengende adresser)
    oneline = re.sub(r"\s+", " ", text)

    for m in _POSTAL_LINE.finditer(oneline):
        before = oneline[max(0, m.start() - 40) : m.start()].lower()
        if _bad_context(before + m.group(0)):
            continue
        street = _shorten_street(m.group(1))
        postal = m.group(2)
        if len(street) < 4 or not postal.isdigit():
            continue
        out.append(
            {
                "address_pattern": street,
                "postal": postal,
                "name": name,
                "source": "bufdir_json",
            }
        )

    # Postboks med postnummer
    for m in re.finditer(
        r"(Postboks\s+\d+[A-Za-z]?)\s*,\s*(\d{4})\s+",
        oneline,
        flags=re.I,
    ):
        out.append(
            {
                "address_pattern": m.group(1).strip(),
                "postal": m.group(2),
                "name": name,
                "source": "bufdir_json",
            }
        )

    # Linjer med «gate, Sted» uten postnummer (krever streng validering i matcher)
    for line in text.split("\n"):
        line = line.strip()
        if not line or re.search(r"\b\d{4}\s+[A-Za-zÆØÅ]", line):
            continue
        if _bad_context(line):
            continue
        cm = _CITY_ONLY.match(line)
        if not cm:
            continue
        street = _shorten_street(cm.group(1).strip())
        if len(street) < 8:
            continue
        if not re.search(r"\d", street) and len(street) < 18:
            continue
        out.append(
            {
                "address_pattern": street,
                "postal": "",
                "name": name,
                "source": "bufdir_json",
            }
        )

    # Enkeltlinje uten komma men med tydelig stedsnavn (f.eks. byggnavn)
    for line in text.split("\n"):
        line = line.strip()
        if not line or "," in line:
            continue
        if _bad_context(line):
            continue
        m = re.match(r"^(?:Adresse:\s*)?(.+)$", line)
        if not m:
            continue
        rest = m.group(1).strip()
        if len(rest) < 16:
            continue
        low = rest.lower()
        if any(
            low.startswith(p)
            for p in (
                "du kan ",
                "kontoret ",
                "vi holder",
                "merk!",
                "på ",
            )
        ):
            continue
        if "sagatunbygget" in low or "bygget i " in low:
            out.append(
                {
                    "address_pattern": rest,
                    "postal": "",
                    "name": name,
                    "source": "bufdir_json",
                }
            )

    return out


def load_bufdir_auto_mappings(bufdir_path: Path) -> list[dict[str, Any]]:
    if not bufdir_path.exists():
        return []
    data = json.loads(bufdir_path.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()
    merged: list[dict[str, Any]] = []
    for office in data.get("offices") or []:
        for m in extract_auto_mappings_from_office(office):
            key = (m["address_pattern"].strip().lower(), (m.get("postal") or "").strip())
            if key in seen:
                continue
            seen.add(key)
            merged.append(m)
    return merged


def merge_mappings(
    manual: list[dict[str, Any]],
    auto: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Manuelle oppføringer først; auto hopper over samme (pattern, postal)."""
    manual_keys = {
        (
            (m.get("address_pattern") or "").strip().lower(),
            (m.get("postal") or "").strip(),
        )
        for m in manual
    }
    out = [dict(m) for m in manual]
    for m in auto:
        key = (
            (m.get("address_pattern") or "").strip().lower(),
            (m.get("postal") or "").strip(),
        )
        if key in manual_keys:
            continue
        out.append(m)
    return out
