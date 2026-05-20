"""SQL-resultatrader → tabular for KI Kollega-diagram (samme kontrakt som SSB: rows, dimensionKeys, valueKey)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


def _cell_json(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def _is_numeric_val(v: Any) -> bool:
    if v is None or isinstance(v, bool):
        return False
    if isinstance(v, (int, float, Decimal)):
        return True
    return False


def sql_rows_to_chart_tabular(
    columns: List[str],
    row_dicts: List[Dict[str, Any]],
    *,
    max_rows: int = 300,
) -> Optional[Dict[str, Any]]:
    """
    Bygg tabular for SSBJsonStatChart dersom minst én numerisk kolonne finnes.
    valueKey velges blant numeriske kolonner (foretrekker navn med sum/total/beløp osv.).
    """
    if not columns or not row_dicts:
        return None
    cols = [str(c) for c in columns]
    rows_out: List[Dict[str, Any]] = []
    for rd in row_dicts[:max_rows]:
        rows_out.append({k: _cell_json(rd.get(k)) for k in cols})

    numeric_cols: List[str] = []
    for k in cols:
        for r in rows_out:
            if _is_numeric_val(r.get(k)):
                numeric_cols.append(k)
                break
    if not numeric_cols:
        return None

    def _score_value_col(k: str) -> tuple:
        kl = k.lower()
        bonus = sum(
            1
            for term in (
                "total",
                "sum",
                "amount",
                "belop",
                "beløp",
                "count",
                "antall",
                "kost",
                "leie",
                "kvm",
                "m2",
                "verdi",
            )
            if term in kl
        )
        return (-bonus, cols.index(k))

    value_key = max(numeric_cols, key=_score_value_col)
    dimension_keys = [k for k in cols if k != value_key]

    if not dimension_keys:
        for i, r in enumerate(rows_out):
            r["#"] = str(i + 1)
        dimension_keys = ["#"]

    return {
        "rows": rows_out,
        "dimensionKeys": dimension_keys,
        "valueKey": value_key,
        "role": None,
    }


def pick_last_chart_from_script_results(sr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Samle alle gyldige diagram-payloads fra unified script_results og returner den siste
    (typisk siste verktøykall med tabell/SSB-data).
    """
    candidates: List[Dict[str, Any]] = []
    for val in sr.values():
        if not isinstance(val, dict):
            continue
        ch = val.get("chart")
        if (
            isinstance(ch, dict)
            and isinstance(ch.get("rows"), list)
            and len(ch["rows"]) > 0
        ):
            candidates.append(
                {
                    "rows": ch["rows"],
                    "dimensionKeys": list(ch.get("dimensionKeys") or []),
                    "valueKey": ch.get("valueKey") or "verdi",
                    "role": ch.get("role"),
                }
            )
            continue
        legacy = val.get("data")
        if isinstance(legacy, list) and len(legacy) > 0 and isinstance(legacy[0], dict):
            row0 = legacy[0]
            dims = [k for k in row0.keys() if k != "verdi"]
            vk = "verdi" if "verdi" in row0 else (dims[0] if len(dims) == 1 else "verdi")
            candidates.append(
                {
                    "rows": legacy,
                    "dimensionKeys": dims,
                    "valueKey": vk,
                    "role": None,
                }
            )
    return candidates[-1] if candidates else None
