"""
Felles property-matching for CSV-import.
Prioritet: lokalisering_id → unit_id_erp → adresse (exact/heuristic/fuzzy) → navn (contains/fuzzy) → aliases.

Se docs/BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md og plan for CSV-heterogenitet.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

import difflib


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    t = (s or "").strip()
    return t if t else None


def _normalize_address_canonical(val: Optional[str]) -> str:
    """Lowercase, fjern punktum/komma."""
    if val is None:
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"[\s\t\r\n]+", " ", s)
    s = re.sub(r"[.,;:-]", "", s)
    return s.strip()


def _normalize_address_heuristic(val: Optional[str]) -> str:
    """Suffix-equivalence: gata→gt, veien→vg."""
    s = _normalize_address_canonical(val)
    s = s.replace("gata", "gt").replace("gaten", "gt")
    s = s.replace("veien", "vg").replace("vegen", "vg")
    return s


def _parse_lokalisering_id(lok_raw: Optional[str]) -> Optional[str]:
    """Hent kode fra 'XXXX - Navn'."""
    if not lok_raw:
        return None
    m = re.match(r"^(\d{4,5})", str(lok_raw).strip())
    return m.group(1) if m else None


def _parse_lokalisering_navn(lok_raw: Optional[str]) -> Optional[str]:
    """Hent navn fra 'XXXX - Navn'."""
    if not lok_raw:
        return None
    s = str(lok_raw).strip()
    if " - " in s:
        part = s.split(" - ", 1)[1].split(",")[0]
        return _norm(part)
    return _norm(s) if s else None


# --- Alias-håndtering (external_data.aliases) ---


def add_property_alias(property_obj: Any, alias: str, source: Optional[str] = None) -> None:
    """
    Legg til alias i properties.external_data.aliases.
    Oppdaterer property_obj i sted (må flag_modified for JSONB).
    """
    alias_clean = _norm(alias)
    if not alias_clean or len(alias_clean) < 2:
        return
    if property_obj.external_data is None:
        property_obj.external_data = {}
    aliases = property_obj.external_data.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = []
    entry = alias_clean
    if source:
        entry = {"alias": alias_clean, "source": source}
    if entry not in aliases and alias_clean not in [a.get("alias", a) if isinstance(a, dict) else a for a in aliases]:
        aliases.append(entry if source else alias_clean)
    property_obj.external_data["aliases"] = aliases


def get_property_aliases(property_obj: Any) -> List[str]:
    """Hent alle alias fra property.external_data.aliases."""
    if not property_obj or not property_obj.external_data:
        return []
    aliases = property_obj.external_data.get("aliases") or []
    if not isinstance(aliases, list):
        return []
    result = []
    for a in aliases:
        if isinstance(a, dict):
            result.append(a.get("alias", ""))
        elif isinstance(a, str):
            result.append(a)
    return [x for x in result if x]


def _name_matches(text: str, name: Optional[str], aliases: List[str]) -> float:
    """Returner score 0-1 for match mot name eller aliases."""
    if not text or len(text) < 2:
        return 0.0
    text_lower = text.lower()
    candidates = [name] if name else []
    candidates.extend(aliases)
    best = 0.0
    for c in candidates:
        if not c:
            continue
        c_lower = c.lower()
        if text_lower == c_lower:
            return 1.0
        if text_lower in c_lower or c_lower in text_lower:
            best = max(best, 0.9)
        s = difflib.SequenceMatcher(None, text_lower, c_lower).ratio()
        best = max(best, s)
    return best


# --- Matching ---


def build_property_index(
    properties: List[Any],
) -> Dict[str, Any]:
    """
    Bygg indekser for rask matching.
    Returnerer dict med: lok_to_props, by_address_norm, by_address_heur, by_name_contains, all_props.
    """
    lok_to_props: Dict[str, List] = {}
    by_address_norm: Dict[str, Any] = {}
    by_address_heur: Dict[str, List] = {}
    by_name_contains: Dict[str, List] = {}

    for p in properties:
        lok = getattr(p, "lokalisering_id", None)
        if lok and _norm(lok):
            lok_to_props.setdefault(str(lok).strip(), []).append(p)

        addr = getattr(p, "address", None) or ""
        if addr:
            can = _normalize_address_canonical(addr)
            if can:
                by_address_norm[can] = p
            heur = _normalize_address_heuristic(addr)
            if heur:
                by_address_heur.setdefault(heur, []).append(p)

        name = getattr(p, "name", None) or ""
        if name and len(name) >= 4:
            name_spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
            words = [w for w in re.split(r"[\s\-]+", name_spaced.lower()) if len(w) >= 4]
            for w in words:
                lst = by_name_contains.setdefault(w, [])
                if p not in lst:
                    lst.append(p)

    return {
        "lok_to_props": lok_to_props,
        "by_address_norm": by_address_norm,
        "by_address_heur": by_address_heur,
        "by_name_contains": by_name_contains,
        "all_props": properties,
    }


def match_property(
    idx: Dict[str, Any],
    *,
    lokalisering_id: Optional[str] = None,
    lokalisering_raw: Optional[str] = None,
    address: Optional[str] = None,
    postal_code: Optional[str] = None,
    city: Optional[str] = None,
    name: Optional[str] = None,
    unit_id_erp: Optional[str] = None,
    radetikett: Optional[str] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Finn eiendom basert på søkekriterier.
    Returnerer (property, method) eller (None, None).

    Prioritet:
    1. lokalisering_id (eller parse fra lokalisering_raw)
    2. unit_id_erp
    3. adresse (exact → heuristic → fuzzy)
    4. navn (contains → fuzzy)
    5. aliases (fuzzy mot radetikett/name)
    """
    lok_id = lokalisering_id or _parse_lokalisering_id(lokalisering_raw)
    lok_navn = _parse_lokalisering_navn(lokalisering_raw) if lokalisering_raw else name
    addr = _norm(address)
    postnr = _norm(postal_code)
    poststed = _norm(city)
    search_name = name or radetikett or lok_navn

    lok_to_props = idx.get("lok_to_props", {})
    by_address_norm = idx.get("by_address_norm", {})
    by_address_heur = idx.get("by_address_heur", {})
    by_name_contains = idx.get("by_name_contains", {})
    all_props = idx.get("all_props", [])

    # Pass 1: lokalisering_id
    if lok_id and lok_id in lok_to_props:
        props = lok_to_props[lok_id]
        return (props[0], "lokalisering_id")

    # Pass 2: unit_id_erp
    if unit_id_erp and _norm(unit_id_erp):
        for p in all_props:
            uerp = getattr(p, "unit_id_erp", None)
            if uerp and str(uerp).strip() == str(unit_id_erp).strip():
                return (p, "unit_id_erp")

    # Pass 3: navn_contains (fra lokalisering-navn)
    if lok_navn and len(lok_navn) >= 3:
        words = [w for w in re.split(r"[\s\-]+", lok_navn.lower()) if len(w) >= 4]
        key = max(words, key=len) if words else lok_navn.lower()
        candidates = by_name_contains.get(key, [])
        if len(candidates) == 1:
            return (candidates[0], "navn_contains")
        if len(candidates) > 1 and (postnr or poststed):
            for p in candidates:
                p_post = _norm(str(getattr(p, "postal_code", None) or ""))
                p_city = (str(getattr(p, "city", None) or "")).strip().upper()
                if postnr and p_post == postnr:
                    return (p, "navn_contains")
                if poststed and p_city and poststed.upper() in p_city:
                    return (p, "navn_contains")
            return (candidates[0], "navn_contains")
        if len(candidates) > 1:
            return (candidates[0], "navn_contains")

    # Pass 4: adresse exact/heuristic
    if addr:
        addr_full = f"{addr} {postnr or ''} {poststed or ''}".strip()
        addr_can = _normalize_address_canonical(addr_full)
        if addr_can and addr_can in by_address_norm:
            return (by_address_norm[addr_can], "adresse_exact")
        addr_can_short = _normalize_address_canonical(addr)
        if addr_can_short and addr_can_short in by_address_norm:
            return (by_address_norm[addr_can_short], "adresse_exact")
        addr_heur = _normalize_address_heuristic(addr)
        if addr_heur and addr_heur in by_address_heur:
            candidates = by_address_heur[addr_heur]
            if len(candidates) == 1:
                return (candidates[0], "adresse_heuristic")

    # Pass 5: adresse fuzzy
    if addr:
        row_can = _normalize_address_canonical(addr)
        if row_can and len(row_can) >= 5:
            best_match, best_score, second_best = None, 0.0, 0.0
            for p in all_props:
                p_addr = getattr(p, "address", None) or ""
                p_can = _normalize_address_canonical(p_addr)
                if not p_can:
                    continue
                s = difflib.SequenceMatcher(None, row_can, p_can).ratio()
                if s > best_score:
                    second_best, best_score, best_match = best_score, s, p
                elif s > second_best:
                    second_best = s
            if best_match and best_score >= 0.85 and (best_score - second_best >= 0.05):
                return (best_match, "adresse_fuzzy")

    # Pass 6: navn fuzzy (inkl. aliases)
    if search_name and len(search_name) >= 4:
        row_name = search_name.lower()
        best_match, best_score, second_best = None, 0.0, 0.0
        for p in all_props:
            p_name = (getattr(p, "name", None) or "").strip().lower()
            aliases = get_property_aliases(p)
            score = _name_matches(row_name, p.name, aliases)
            if score > best_score:
                second_best, best_score, best_match = best_score, score, p
            elif score > second_best:
                second_best = score
        if best_match and best_score >= 0.80 and (best_score - second_best >= 0.05):
            return (best_match, "navn_fuzzy")

    return (None, None)
