"""
Flater SSB PxWebApi json-stat2 til tabellrader for diagram (samme konsept som frontend flattenJsonStat2).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def flatten_json_stat2_for_chart(
    dataset: Dict[str, Any],
    *,
    max_rows: int = 2000,
    value_key: str = "verdi",
) -> Optional[Dict[str, Any]]:
    """Returnerer JSON-serialiserbar chart-payload: rows, dimensionKeys, valueKey, role."""
    value = dataset.get("value")
    id_dims = dataset.get("id")
    dimension = dataset.get("dimension") or {}
    if not isinstance(value, list) or not id_dims or not isinstance(id_dims, list):
        return None

    dims: List[Dict[str, Any]] = []
    for key in id_dims:
        d = dimension.get(key) or {}
        if not isinstance(d, dict):
            d = {}
        cat = d.get("category") or {}
        if not isinstance(cat, dict):
            cat = {}
        idx = cat.get("index")
        lbl_raw = cat.get("label")
        codes: List[str] = []
        code_to_label: Dict[str, str] = {}

        if isinstance(idx, dict):
            codes = sorted(idx.keys(), key=lambda c: idx.get(c, 0))
            lbl_map = lbl_raw if isinstance(lbl_raw, dict) else {}
            for code in codes:
                code_to_label[str(code)] = str(lbl_map.get(code, code))
        elif isinstance(idx, list):
            codes = [str(x) for x in idx]
            lbl_arr = lbl_raw if isinstance(lbl_raw, list) else []
            for i, code in enumerate(codes):
                code_to_label[code] = str(lbl_arr[i]) if i < len(lbl_arr) else code
        else:
            continue

        dims.append({"key": key, "codes": codes, "code_to_label": code_to_label})

    if not dims:
        return None

    rows: List[Dict[str, Any]] = []
    val_idx = 0

    def _coerce_num(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v) if isinstance(v, float) or (isinstance(v, int) and not isinstance(v, bool)) else v
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    def walk(di: int, acc: List[str]) -> None:
        nonlocal val_idx
        if len(rows) >= max_rows:
            return
        if di >= len(dims):
            if val_idx >= len(value):
                return
            v = value[val_idx]
            row: Dict[str, Any] = {value_key: _coerce_num(v)}
            for i, dim in enumerate(dims):
                code = acc[i]
                row[dim["key"]] = dim["code_to_label"].get(code, code)
            rows.append(row)
            val_idx += 1
            return
        dim = dims[di]
        for code in dim["codes"]:
            if len(rows) >= max_rows:
                return
            walk(di + 1, acc + [code])

    walk(0, [])

    role_out: Optional[Dict[str, List[str]]] = None
    role_raw = dataset.get("role")
    if isinstance(role_raw, dict):
        role_out = {}
        for rk, rv in role_raw.items():
            if isinstance(rv, list):
                role_out[str(rk)] = [str(x) for x in rv]

    return {
        "rows": rows,
        "dimensionKeys": [str(k) for k in id_dims],
        "valueKey": value_key,
        "role": role_out,
    }
