"""
Query normalizer for KI Kollega – robust forståelse av brukerinput.

Håndterer skrivefeil, forkortelser og synonymer slik at brukere får riktige svar
selv når de ikke skriver helt presist.
"""

import re
from typing import List

# Vanlige skrivefeil: feil -> riktig
COMMON_TYPOS = {
    "familievernkontoor": "familievernkontor",
    "eiendomer": "eiendommer",
    "kvadradmeter": "kvadratmeter",
}

# BEFS-synonymer for routing og søk (kort form -> kanonisk form)
BEFS_SYNONYMS = {
    # Eiendomstyper
    "fvk": "familievernkontor",
    "fv": "familievern",
    "familievernkontoor": "familievernkontor",
    "bup": "bup",
    "barnevern": "barnevern",
    "krise": "krise",
    # Leietakere/parter
    "leietaker": "parter",
    "leietakere": "parter",
    "leverandør": "parter",
    "leverandører": "parter",
    # Kostnad
    "billigste per kvm": "lavest kostnad per kvm",
    "pris per kvm": "kostnad per kvm",
    "kvadratmeter": "kvm",
    "kvadratmetere": "kvm",
}

# For property lookup: brukerterm -> liste av søkeord å prøve (i rekkefølge)
PROPERTY_LOOKUP_EXPANSIONS = {
    "fvk": ["familievernkontor", "familievern", "fvk"],
    "fv": ["familievern", "familievernkontor", "fv"],
    "familievernkontor": ["familievernkontor", "familievern"],
    "familievern": ["familievern", "familievernkontor"],
    "barnevern": ["barnevern", "barnevernsinstitusjon"],
    "bup": ["bup", "BUP"],
    "krise": ["krise", "krisesenter"],
}


def normalize_query(text: str) -> str:
    """
    Normaliser brukerinput for robust matching.
    - Strip, collapse whitespace
    - Lowercase for matching
    - Fjern vanlige skrivefeil
    """
    if not text or not isinstance(text, str):
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.lower()
    # Erstatt vanlige skrivefeil (sjekk hele ord)
    words = t.split()
    corrected = []
    for w in words:
        corrected.append(COMMON_TYPOS.get(w, w))
    return " ".join(corrected)


def expand_query_terms(text: str) -> str:
    """
    Utvid synonyme termer i teksten for routing og søk.
    Erstatter kjente BEFS-forkortelser/synonymer med kanoniske former.
    """
    if not text:
        return ""
    normalized = normalize_query(text)
    result = normalized
    # Sorter etter lengde (lengste først) for å matche "billigste per kvm" før "kvm"
    for short, canonical in sorted(BEFS_SYNONYMS.items(), key=lambda x: -len(x[0])):
        # Bruk word boundaries for å unngå å erstatte deler av ord
        pattern = r"\b" + re.escape(short) + r"\b"
        result = re.sub(pattern, canonical, result, flags=re.IGNORECASE)
    return result


def get_search_terms_for_property_lookup(user_term: str) -> List[str]:
    """
    Returner liste av søkeord (original + synonymer) for lookup_properties.
    Eksempel: "fvk" -> ["familievernkontor", "familievern", "fvk"]
    Hvis brukeren skriver en lengre setning (f.eks. "finn eiendommer med barnevern"),
    ekstraheres kjent term fra teksten.
    """
    if not user_term or len(user_term.strip()) < 2:
        return []
    term = user_term.strip().lower()
    # Sjekk om vi har eksplisitt ekspansjon
    if term in PROPERTY_LOOKUP_EXPANSIONS:
        return PROPERTY_LOOKUP_EXPANSIONS[term]
    # Sjekk om teksten inneholder et kjent term (f.eks. "finn eiendommer med barnevern" -> "barnevern")
    for known_term, expansions in PROPERTY_LOOKUP_EXPANSIONS.items():
        if known_term in term:
            return expansions
    # Standard: bruk termen som den er, evt. utvid via BEFS_SYNONYMS
    canonical = BEFS_SYNONYMS.get(term, term)
    if canonical != term:
        return [canonical, term]
    return [term]
