"""
Felles konstanter for GL-transaksjoner og husleie-kategorisering.
Brukes av gl-financial-bulk, financial-summary, rent-gap m.m.
"""
from __future__ import annotations

from sqlalchemy import or_

# Eksplisitte kontonavn som regnes som husleie (leiekostnader)
LEASE_ACCOUNT_NAMES = frozenset({
    "Leie lokaler fra Statsbygg",
    "Leie lokaler andre utleiere",
    "Leie parkeringsplass",
    "Leie av lager/naust/garsjer og lignende",
    "Husleie",
})


def gl_lease_filter(account_name_column):
    """
    SQLAlchemy-filter for husleie-kontoer. Bruk: .where(gl_lease_filter(GLTransaction.account_name))
    """
    conditions = [account_name_column == name for name in LEASE_ACCOUNT_NAMES]
    conditions.append(account_name_column.ilike("Leie %"))
    return or_(*conditions)


def is_lease_account(account_name: str | None) -> bool:
    """
    Sjekk om account_name regnes som husleie/leiekostnad.
    Inkluderer eksplisitte navn + mønster 'Leie ' (starter med Leie + mellomrom).
    Ekskluderer f.eks. 'Fellesutgifter andre utleiere' (utleiere ≠ leie som kostnadstype).
    """
    if not account_name or not str(account_name).strip():
        return False
    s = str(account_name).strip()
    if s in LEASE_ACCOUNT_NAMES:
        return True
    # "Leie lokaler", "Leie parkeringsplass", "Leie av lager..." osv.
    if s.lower().startswith("leie "):
        return True
    if s.lower() == "husleie":
        return True
    return False
