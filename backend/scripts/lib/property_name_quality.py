"""
Delt logikk for eiendomsnavn vs. adresse (brukes av enrich, audit, matching).
"""
from __future__ import annotations

import re
from typing import Optional

ADDRESS_PATTERN = re.compile(r",\s*\d{4}\s+", re.IGNORECASE)


def _normalize(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def is_address_only_name(name: Optional[str], address: Optional[str]) -> bool:
    """True hvis name ser ut som kun adresse (ingen egentlig eiendomsnavn)."""
    if not name or not name.strip():
        return False
    name = name.strip()
    addr = (address or "").strip()

    if addr and _normalize(name) == _normalize(addr):
        return True

    if ADDRESS_PATTERN.search(name):
        if addr and addr.lower() in name.lower():
            return True
        if " - " not in name and len(name) < 80:
            return True

    if addr and name.lower().startswith(addr.lower()):
        rest = name[len(addr) :].strip()
        if not rest or re.match(r"^[,\s\d]+", rest):
            return True

    return False


def should_sync_name_from_bufdir(
    current_name: Optional[str],
    address: Optional[str],
    official_bufdir_name: str,
) -> bool:
    """Om vi trygt kan sette Property.name til Bufdir sitt offisielle navn."""
    if not official_bufdir_name or not official_bufdir_name.strip():
        return False
    official = official_bufdir_name.strip()
    cn = (current_name or "").strip()
    if not cn:
        return True
    if _normalize(cn) == _normalize(address or ""):
        return True
    if is_address_only_name(current_name, address):
        from difflib import SequenceMatcher

        return SequenceMatcher(None, _normalize(cn), _normalize(official)).ratio() < 0.75
    return False
