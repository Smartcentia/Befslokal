#!/usr/bin/env python3
"""
Validerer costs2025 CSV-er mot manifest (pivot-total vs erpGrandTotalNok,
og utvalgte kategorier mot aggregert.csv). Matcher logikken i parseInnkjopCsv.ts.
Kjør fra repo-rot: python3 frontend/scripts/validate_costs2025.py
eller: cd frontend && python3 scripts/validate_costs2025.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _frontend_root() -> Path:
    p = Path(__file__).resolve().parent.parent
    return p


def _data_dir() -> Path:
    return _frontend_root() / "public" / "data" / "costs2025"


PIVOT_SECTION_HEADERS = frozenset(
    {
        "Leie lokaler andre utleiere",
        "Leie lokaler fra Statsbygg",
        "Fellesutgifter (BAD) Statsbygg",
        "Fellesutgifter andre utleiere",
        "Strøm og oppvarming",
        "Renhold lokaler",
        "Reparasjon og vedlikehold leide lokaler",
        "Annen kostnad lokaler",
        "Leie parkeringsplass",
        "Vakthold lokaler",
        "Vaktmestertjenester",
        "Renovasjon, vann, avløp o.l.",
        "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
        "Reparasjon og vedlikehold av verktøy og maskiner, inkl serviceavtaler",
        "Reparasjon og vedlikehold av datautstyr, inkl. serviceavtaler",
        "Fellesutgifter Statsbygg - indre vedlikehold",
    }
)


def parse_nok(s: str) -> float:
    if not s or not str(s).strip():
        return 0.0
    cleaned = str(s).replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def detect_delimiter(first_line: str) -> str:
    semis = first_line.count(";")
    commas = first_line.count(",")
    return ";" if semis >= commas else ","


def parse_pivot_detail_csv(text: str) -> list[tuple[str, str, float]]:
    """Returnerer liste av (category, institution, total)."""
    lines = text.splitlines()
    delim = detect_delimiter(lines[0] if lines else ";")
    header_idx = next((i for i, l in enumerate(lines) if "Radetiketter" in l), -1)
    if header_idx == -1:
        return []

    rows: list[tuple[str, str, float]] = []
    current_category = ""

    for i in range(header_idx + 1, len(lines)):
        cols = lines[i].split(delim)
        if not any(c.strip() for c in cols):
            continue

        name = cols[0].strip() if cols else ""

        if name.startswith("Leie av lokaler og tilknyttede"):
            continue
        if name.startswith("Totalsum"):
            continue

        if not name:
            bufdir_amt = parse_nok(cols[6]) if len(cols) > 6 else 0
            total_amt = parse_nok(cols[7]) if len(cols) > 7 else 0
            if bufdir_amt != 0 or total_amt != 0:
                rows.append(
                    (
                        current_category,
                        "Bufdir",
                        total_amt if total_amt else bufdir_amt,
                    )
                )
            continue

        has_amount = any(parse_nok(c) != 0 for c in cols[1:])
        if not has_amount:
            if name in PIVOT_SECTION_HEADERS:
                current_category = name
            continue

        total = parse_nok(cols[7]) if len(cols) > 7 else 0
        rows.append((current_category, name, total))

    return rows


def parse_aggregert_csv(text: str) -> dict[str, float]:
    lines = text.splitlines()
    delim = detect_delimiter(lines[0] if lines else ";")
    header_idx = next((i for i, l in enumerate(lines) if "Radetiketter" in l), -1)
    if header_idx == -1:
        return {}

    out: dict[str, float] = {}
    for i in range(header_idx + 1, len(lines)):
        cols = lines[i].split(delim)
        if not any(c.strip() for c in cols):
            continue
        name = cols[0].strip() if cols else ""
        if not name:
            continue
        if name.startswith("Leie av lokaler og tilknyttede"):
            continue
        if name in ("Kontor og administrasjon", "IKT"):
            continue
        if not any(parse_nok(c) != 0 for c in cols[1:]):
            continue
        out[name] = parse_nok(cols[7]) if len(cols) > 7 else 0
    return out


def main() -> int:
    data_dir = _data_dir()
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.is_file():
        print("FEIL: manifest.json mangler:", manifest_path, file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    erp = float(manifest["erpGrandTotalNok"])

    pivot_path = data_dir / "leie_av_lokaler.csv"
    raw = pivot_path.read_bytes()
    try:
        text = raw.decode("windows-1252")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    pivot_rows = parse_pivot_detail_csv(text)
    pivot_sum = sum(t for _, _, t in pivot_rows)

    if abs(pivot_sum - erp) > 2000:
        print(f"FEIL: pivot-sum {pivot_sum:,.0f} vs manifest erpGrandTotalNok {erp:,.0f}", file=sys.stderr)
        return 1

    agg_path = data_dir / "aggregert.csv"
    agg_text = agg_path.read_bytes().decode("windows-1252")
    agg = parse_aggregert_csv(agg_text)

    for cat in ("Leie lokaler fra Statsbygg", "Strøm og oppvarming"):
        cat_sum = sum(t for c, _, t in pivot_rows if c == cat)
        if cat not in agg:
            print(f"ADVARSEL: kategori {cat!r} finnes ikke i aggregert.csv", file=sys.stderr)
            continue
        if abs(agg[cat] - cat_sum) > 10_000:
            print(
                f"FEIL: {cat}: aggregert {agg[cat]:,.0f} vs pivot {cat_sum:,.0f}",
                file=sys.stderr,
            )
            return 1

    print("OK: pivot-total matcher manifest (±2000 kr); Statsbygg-leie og strøm matcher aggregert (±10 000 kr).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
