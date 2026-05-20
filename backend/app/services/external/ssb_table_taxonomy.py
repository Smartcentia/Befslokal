"""
Kategorisering av kuraterte SSB-tabeller (barnevern / familievern) for UI og JSON.

Stabile nøkler (API/JSON): kostra, melding, tiltak, institusjon, utdanning, utenforskap, familievern, annet
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

# Rekkefølge ved flere treff og for primær gruppering i UI
CATEGORY_ORDER: Tuple[str, ...] = (
    "kostra",
    "melding",
    "tiltak",
    "institusjon",
    "utdanning",
    "utenforskap",
    "familievern",
    "annet",
)

# Eksplisitte tabell-ID-er som ofte skal leses som én hovedtype (supplerer tekstmønstre)
TABLE_ID_HINTS: Tuple[Tuple[str, str], ...] = (
    ("10674", "melding"),
    ("12845", "tiltak"),
    ("13350", "utdanning"),
    ("13346", "utdanning"),
    ("12423", "utenforskap"),
    ("13556", "utenforskap"),
    ("13563", "utenforskap"),
)

_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("kostra", ("kostra",)),
    ("melding", ("melding", "meldingar")),
    ("tiltak", ("tiltak", "plassering", "fosterhjem", "omsorgsovertak")),
    ("institusjon", ("institusjon", "opphalds", "opphold")),
    ("utdanning", ("utdanning", "skole", "grunnsk", "vidareg", "videreg")),
    (
        "utenforskap",
        ("neet", "utenforskap", "prioritert arbeidsstyrkestatus"),
    ),
    ("familievern", ("familievern",)),
)


def classify_ssb_table(
    label: Optional[str],
    variable_names: Optional[Sequence[str]],
    table_id: str = "",
) -> List[str]:
    s = (label or "").lower()
    v = " ".join(str(x).lower() for x in (variable_names or []))
    blob = f"{s} {v}"

    found: List[str] = []
    for key, needles in _RULES:
        if any(n in blob for n in needles):
            found.append(key)

    tid = (table_id or "").strip()
    for pid, hint in TABLE_ID_HINTS:
        if tid == pid and hint not in found:
            found.append(hint)

    order_map = {k: i for i, k in enumerate(CATEGORY_ORDER)}
    found = sorted(set(found), key=lambda k: order_map.get(k, 99))

    if not found:
        return ["annet"]
    return found
