"""
Party Health Score – aggregerer tilgjengelig datakilde (BRREG, konkurs-sjekk,
årsregnskap, due-diligence) til én score 1–4 og en farge-label.

    1 → GRØNN    (Lav risiko – normal drift)
    2 → GUL      (Moderat – krever oppfølging)
    3 → ORANSJE  (Høy – ta kontakt / vurder tilsyn)
    4 → RØD      (Kritisk – øyeblikkelig handling)

Kan kalles uten DB-tilgang – tar kun `external_data`-dict som input.
"""

from __future__ import annotations
from typing import Any

_LABELS = {1: "GRØNN", 2: "GUL", 3: "ORANSJE", 4: "RØD"}

# ── Norwegian display labels ─────────────────────────────────────────────────
_SCORE_META = {
    1: {"label": "GRØNN",   "emoji": "✅", "category": "Normal drift"},
    2: {"label": "GUL",     "emoji": "⚠️",  "category": "Krever oppfølging"},
    3: {"label": "ORANSJE", "emoji": "🔶", "category": "Høy risiko"},
    4: {"label": "RØD",     "emoji": "🚨", "category": "Kritisk risiko"},
}


def compute_health_score(external_data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Compute a 1-4 health score from whatever fields exist in external_data.
    Pure function – no I/O, always returns a valid dict.
    """
    if not external_data:
        return {
            "score": 1,
            **_SCORE_META[1],
            "factors": [],
            "data_sources": [],
            "data_quality": "no_data",
        }

    score = 1
    factors: list[str] = []
    data_sources: list[str] = []

    # ── 1. Konkurs status (nattlig BRREG-sjekk) ──────────────────────────────
    ks = external_data.get("konkurs_status") or {}
    if ks:
        data_sources.append("konkurs_sjekk")
        rl = ks.get("risk_level", "OK")
        if rl == "CRITICAL":
            score = 4
            factors.extend(ks.get("risk_flags") or [])
        elif rl == "WARNING":
            score = max(score, 3)
            factors.extend(ks.get("risk_flags") or [])

    # ── 2. BRREG rå-flagg (fra enhet-data) ──────────────────────────────────
    # Kun brukt som backup hvis konkurs_status ikke er kjørt ennå
    brreg = external_data.get("brreg_enhet") or {}
    if brreg:
        data_sources.append("brreg")
        if brreg.get("konkurs") and score < 4:
            score = 4
            factors.append("Konkurs registrert (Brønnøysund)")
        if brreg.get("underTvangsavviklingEllerTvangsopplosning") and score < 4:
            score = max(score, 4)
            factors.append("Under tvangsoppløsning")
        if brreg.get("underAvvikling") and score < 3:
            score = max(score, 3)
            factors.append("Under avvikling")
        # Slettet: bare legg til hvis konkurs_status ikke allerede dekker det
        if brreg.get("slettedato") and not ks.get("risk_flags"):
            score = max(score, 4)
            factors.append(f"Slettet {brreg['slettedato']}")

    # ── 3. Due Diligence ─────────────────────────────────────────────────────
    dd = external_data.get("due_diligence_report") or {}
    if dd:
        data_sources.append("due_diligence")
        rl = dd.get("risk_level", "")
        if rl == "HØY":
            score = max(score, 3)
            factors.append("Høy risikovurdering (Due Diligence)")
        elif rl == "MIDDELS":
            score = max(score, 2)
            factors.append("Middels risikovurdering (Due Diligence)")
        # Legg til røde flagg (maks 2)
        for flag in (dd.get("red_flags") or [])[:2]:
            f = f"DD: {flag}"
            if f not in factors:
                factors.append(f)

    # ── 4. Finansiell helse (årsregnskap) ────────────────────────────────────
    regnskap_list = external_data.get("aarsregnskap") or []
    if isinstance(regnskap_list, list) and regnskap_list:
        data_sources.append("regnskap")
        latest = regnskap_list[0]

        soliditet = latest.get("soliditet")
        if soliditet is not None:
            if soliditet < 5:
                score = max(score, 3)
                factors.append(f"Kritisk lav soliditet: {soliditet:.1f}%")
            elif soliditet < 15:
                score = max(score, 2)
                factors.append(f"Lav soliditet: {soliditet:.1f}%")

        driftsmargin = latest.get("driftsmargin")
        if driftsmargin is not None:
            if driftsmargin < -15:
                score = max(score, 3)
                factors.append(f"Negativt driftsresultat: {driftsmargin:.1f}%")
            elif driftsmargin < -5:
                score = max(score, 2)
                factors.append(f"Svakt driftsresultat: {driftsmargin:.1f}%")

        # Trend – negativt årsresultat over flere år
        if len(regnskap_list) >= 2:
            years_checked = min(len(regnskap_list), 3)
            neg_years = sum(
                1 for r in regnskap_list[:years_checked]
                if (r.get("net_income") or 0) < 0
            )
            if neg_years >= 2:
                score = max(score, 2)
                factors.append(
                    f"Negativt årsresultat {neg_years}/{years_checked} siste år"
                )

    # ── 5. Data quality indicator ────────────────────────────────────────────
    n_sources = len(data_sources)
    if n_sources >= 3:
        dq = "høy"
    elif n_sources >= 1:
        dq = "middels"
    else:
        dq = "lav"

    # Dedupliser faktorer, maks 5
    seen: set[str] = set()
    unique_factors: list[str] = []
    for f in factors:
        if f not in seen:
            seen.add(f)
            unique_factors.append(f)
    unique_factors = unique_factors[:5]

    return {
        "score": score,
        **_SCORE_META[score],
        "factors": unique_factors,
        "data_sources": data_sources,
        "data_quality": dq,
    }
