"""
Sentral CSV-kolonnemapping for BEFS.
Se docs/BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md seksjon 8.1.

Struktur: source_key -> { csv_header: (db_field, normalizer) }
- db_field: BEFS-felt (kan være nøstet, f.eks. "amount.amount_per_year")
- normalizer: None eller funksjonsnavn fra NORMALIZERS
"""
from typing import Any, Callable, Dict, Optional, Tuple, Union

# Normalizers – enkle hjelpefunksjoner
def _parse_currency(val: Any) -> Optional[float]:
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    s = str(val).replace(" ", "").replace("\xa0", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_int(val: Any) -> Optional[int]:
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        s = str(val).replace(",", ".").replace(" ", "")
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _normalize_id(val: Any) -> Optional[str]:
    """Normaliser ERP/EnhetID (Dim1, unit_id_erp)."""
    if val is None:
        return None
    s = str(val).strip().replace("\u00A0", " ")
    if not s or s.lower() in ("", "nan", "none", "null"):
        return None
    if s.endswith(".0") and s[:-2].isdigit():
        return s[:-2]
    return s


def _identity(val: Any) -> Any:
    return val


# Eksporterte normalizers for bruk i schema
NORMALIZERS: Dict[str, Callable] = {
    "parse_currency": _parse_currency,
    "parse_int": _parse_int,
    "normalize_id": _normalize_id,
    "identity": _identity,
}


# Eie1212 – semikolon, lowercase headers
EIE1212_SCHEMA: Dict[str, Tuple[str, Optional[str]]] = {
    "lokalisering": ("_lokalisering_raw", None),  # Parse til lokalisering_id + name
    "adresselinje 1": ("address", None),
    "adresse og postnummer": ("_postal_raw", None),
    "poststed": ("city", None),
    "avtalenavn": ("name", None),
    "areal": ("total_area", "parse_currency"),
    "type lokasjon": ("usage", None),
    "tomteareal": ("land_area", "parse_currency"),
    "lok: distrikt": ("region", None),  # Normaliser via region_mapping
    "kommunenavn": ("municipality", None),
    "startdato": ("start_date", None),  # DD.MM.YYYY
    "sluttdato": ("end_date", None),
    "status": ("status", None),
    "kpi-justert kontraktsleie til okt 2025": ("amount.amount_per_year", "parse_currency"),
    "elements": ("external_data.master_data.archive_name", None),
}


# Oversikt bygg og eiendom / Eiendomsportefølje
OVERSIKT_BYGG_SCHEMA: Dict[str, Tuple[str, Optional[str]]] = {
    "Lokalisering": ("_lokalisering_raw", None),
    "Adresselinje 1": ("address", None),
    "Postnr": ("postal_code", None),
    "Poststed": ("city", None),
    "Målgruppe": ("affiliation", None),
    "Målgruppe ": ("affiliation", None),
    "Antall G/K - plasser": ("approved_places", "parse_int"),
    "Antall budsjetterte plasser": ("budgeted_places", "parse_int"),
    "Hjemmel §": ("legal_basis", None),
    "Kontraktsleie": ("amount.amount_per_year", "parse_currency"),
    "Kontraktsleie ved oppstart (per år)": ("amount.amount_per_year", "parse_currency"),
    "KPI-justert kontraktsleie til okt 2025": ("amount.amount_per_year", "parse_currency"),
    "Indre vedlikehold": ("external_data.internal_maintenance_cost", "parse_currency"),
    "KPI-justert indre vedlikehold": ("external_data.internal_maintenance_cost", "parse_currency"),
    "Felleskostnader": ("external_data.common_costs", "parse_currency"),
    "KPI-justert: Felleskostnader": ("external_data.common_costs", "parse_currency"),
    "Årlig prisjusteringsfaktaktor": ("external_data.regulation_type", None),
    "leieregulering": ("external_data.regulation_type", None),
    "adgang til forlengelse og vilkår": ("external_data.extension_terms", None),
    "Adgang til forlengelse og vilkår": ("external_data.extension_terms", None),
    "Egnethet lokalisering": ("external_data.egnethet_lokalisering", "parse_int"),
    "Egnethet bygg": ("external_data.egnethet_bygg", "parse_int"),
    "Avtalenavn": ("_avtalenavn", None),
}


# Kontant OK1 (Xledger) – gl_transactions
OK1_GL_SCHEMA: Dict[str, str] = {
    "BA": "ba_code",
    "BA(T)": "ba_name",
    "Regioner": "region_code",
    "Regioner(T)": "region_name",
    "Avdeling": "department_code",
    "Avdeling(T)": "department_name",
    "Dim 2": "dim2_code",
    "Dim 2(T)": "dim2_name",
    "Formål": "purpose_code",
    "Formål(T)": "purpose_name",
    "Konto": "account_code",
    "Konto(T)": "account_name",
    "Bilagsnr": "invoice_number",
    "Kontantbeløp": "amount",
    "Kont.periode": "period",
    "Statskonto": "state_account",
    "Resk.nr": "supplier_id",
    "Resk.nr(T)": "supplier_name",
}


# Eiendomfebruar (Visma/Agresso) – gl_transactions
# Format: semikolonseparert (;), latin-1, norsk desimalskilletegn (komma), mellomrom som tusensep
EIENDOM_GL_SCHEMA: Dict[str, str] = {
    "BA":                    "ba_code",
    "Bilagsnr":              "invoice_number",
    "Bilagsdato":            "_transaction_date_raw",
    "År":                    "_year_raw",
    "Periode":               "period",
    "Innkjøpskategorier":    "innkjopskategori_kode",
    "Innkjøpskategorier(T)": "innkjopskategori_navn",
    "Underkategorier":       "underkategori_kode",
    "Underkategorier(T)":    "underkategori_navn",
    "Konto":                 "account_code",
    "Konto(T)":              "account_name",
    "Region":                "region_name",       # stor R = regionnavn
    "Dim1":                  "department_code",
    "Dim1(T)":               "department_name",
    "Dim2":                  "dim2_code",
    "Dim2(T)":               "dim2_name",
    "Dim3":                  "purpose_code",
    "Dim4":                  "state_account",
    "Dim5":                  "dim5_code",
    "Dim6":                  "dim6_code",
    "Dim7":                  "dim7_code",
    "AV":                    "av_konto",
    "Tekst":                 "description",
    "Beløp":                 "amount",
    "Resk.nr":               "supplier_id",
    "Resk.nr(T)":            "supplier_name",
}


# Innkjøpsanalyse – radetikett + region-kolonner
INNKJOEPSANALYSE_REGION_COLUMNS = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir"]


# Institusjons-CSV (barnevernsinstitusjoner med plasser)
# Merk: Kolonnenavn kan variere mellom CSV-kilder – alle varianter listes
INSTITUSJONER_SCHEMA: Dict[str, Tuple[str, Optional[str]]] = {
    "Region": ("region", None),
    "Målgruppe": ("affiliation", None),
    "Enhetsnr.": ("lokalisering_id", "normalize_id"),
    "Enhetsnr": ("lokalisering_id", "normalize_id"),
    # Institusjonsnavn – flere mulige kolonnenavn
    "Enhetens/Institusjonens navn": ("name", None),
    "Enhetens navn": ("name", None),
    "Institusjonens navn": ("name", None),
    "Institusjonsnavn": ("name", None),
    "Avdelingens koststed": ("department_code", "normalize_id"),
    "Avdelingens koststed ": ("department_code", "normalize_id"),
    "Navn på avdeling": ("unit_name", None),
    "Avdelingsnavn": ("unit_name", None),
    "Antall kvalitetssikrede institusjonsplasser avd. pr. 01.01": ("approved_places", "parse_int"),
    "Antall kvalitetssikrede plasser": ("approved_places", "parse_int"),
    "Antall budsjetterte institusjonsplasser avd. per 01.01": ("budgeted_places", "parse_int"),
    "Antall budsjetterte plasser": ("budgeted_places", "parse_int"),
}


# e-don2 / BIRK
EDON2_SCHEMA: Dict[str, Tuple[str, Optional[str]]] = {
    "Lokasjonskode": ("lokalisering_id", None),
    "EnhetID": ("unit_id_erp", "normalize_id"),
    "Enhetsnavn": ("name", None),
    "Adresse": ("address", None),
    "Enhetskorttype": ("unit_short_type", None),
    "TilhørighetEnhetID": ("parent_unit_id_erp", "normalize_id"),
}


# Samlet register
CSV_SOURCE_SCHEMAS: Dict[str, Dict] = {
    "eie1212": EIE1212_SCHEMA,
    "oversikt_bygg": OVERSIKT_BYGG_SCHEMA,
    "eiendomsportefolje": OVERSIKT_BYGG_SCHEMA,  # Samme schema
    "institusjoner": INSTITUSJONER_SCHEMA,
    "kontant_ok1": OK1_GL_SCHEMA,
    "kontant_eiendom": EIENDOM_GL_SCHEMA,
    "edon2": EDON2_SCHEMA,
}


def get_schema(source_key: str) -> Optional[Dict]:
    """Hent schema for en kilde."""
    return CSV_SOURCE_SCHEMAS.get(source_key)


def _find_mapping(schema: dict, csv_header: str) -> Optional[Union[Tuple, str]]:
    """Finn mapping for csv_header (case-insensitive, strip)."""
    h = csv_header.strip()
    h_lower = h.lower()
    for k, v in schema.items():
        if k.strip().lower() == h_lower:
            return v
    return None


def map_row(row: dict, source_key: str, normalize_headers: bool = True) -> dict:
    """
    Map en CSV-rad til BEFS-felt ved hjelp av schema.
    normalize_headers: lowercase og strip headers i row før lookup.
    """
    schema = get_schema(source_key)
    if not schema:
        return {}

    result = {}
    for csv_header, row_val in row.items():
        mapping = _find_mapping(schema, csv_header)
        if mapping is None:
            continue

        if isinstance(mapping, tuple):
            db_field, normalizer_name = mapping
            if normalizer_name and normalizer_name in NORMALIZERS:
                try:
                    row_val = NORMALIZERS[normalizer_name](row_val)
                except Exception:
                    pass
        else:
            db_field = mapping  # GL-schema bruker bare streng

        if row_val is not None and row_val != "":
            result[db_field] = row_val

    return result
