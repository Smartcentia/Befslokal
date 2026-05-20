"""
Generering av arkivkode (kontrakter) og referansekode (parties).
Se docs/ARKIVKODE_OG_REFERANSEKODE_STANDARD.md.
"""
from typing import Optional


# Enhetlige kontraktstyper
CONTRACT_CATEGORIES = (
    "Leiekontrakt",
    "Tilleggskontrakt",
    "Serviceavtale",
    "Parkeringsavtale",
    "Annet",
)

# Mapping fra kildetekst til standard category
CATEGORY_MAPPING = {
    "leiekontrakt": "Leiekontrakt",
    "leieavtale": "Leiekontrakt",
    "hovedkontrakt": "Leiekontrakt",
    "hovedleiekontrakt": "Leiekontrakt",
    "tilleggskontrakt": "Tilleggskontrakt",
    "tillegg": "Tilleggskontrakt",
    "serviceavtale": "Serviceavtale",
    "vaktmester": "Serviceavtale",
    "renhold": "Serviceavtale",
    "parkeringsavtale": "Parkeringsavtale",
    "parkering": "Parkeringsavtale",
    "konkurranse": "Annet",
    "kravspes.": "Annet",
    "fil mangler": "Annet",
}


def normalize_contract_category(source: Optional[str]) -> Optional[str]:
    """Map kildetekst til enhetlig kontraktstype."""
    if not source or not isinstance(source, str):
        return None
    key = source.strip().lower()
    return CATEGORY_MAPPING.get(key, "Annet")


def generate_archive_code(
    lokalisering_id: str,
    date_str: str,
    seq: str = "01",
    org: str = "BUF",
) -> str:
    """
    Generer arkivkode for kontrakt.
    Format: BUF-LOK-YYYYMMDD-NN
    Eksempel: BUF-6125-20241014-01
    """
    lok = (lokalisering_id or "").strip()
    if not lok:
        raise ValueError("lokalisering_id er påkrevd for arkivkode")
    # Normaliser dato til YYYYMMDD
    if len(date_str) == 10 and "-" in date_str:  # YYYY-MM-DD
        date_str = date_str.replace("-", "")
    elif len(date_str) == 10 and "." in date_str:  # DD.MM.YYYY
        parts = date_str.split(".")
        if len(parts) == 3:
            date_str = f"{parts[2]}{parts[1]}{parts[0]}"
    seq_padded = str(seq).zfill(2) if seq else "01"
    return f"{org.upper()}-{lok}-{date_str}-{seq_padded}"


def generate_reference_code(seq: int, org: str = "BUF") -> str:
    """
    Generer referansekode for party.
    Format: BUF-P-NNNNNN
    Eksempel: BUF-P-000001
    """
    return f"{org.upper()}-P-{str(seq).zfill(6)}"
