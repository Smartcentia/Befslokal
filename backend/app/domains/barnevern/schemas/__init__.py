"""Pydantic schemas for barnevern-modulen."""

from pydantic import BaseModel
from typing import Dict, List, Optional


class RegionSimulation(BaseModel):
    """Simuleringsresultat per region."""
    region: str
    approved_places: int
    brukte_plasser: int
    ubrukte_plasser: int
    kost_brukte: float
    kost_ubrukte: float
    total_kostnad: float
    annual_cost_region: float


class SimulationResult(BaseModel):
    """Total simuleringsresultat."""
    year: int
    usage_pct: float
    egenandel_maaned: float
    egenandel_aar: float
    by_region: List[RegionSimulation]
    total_approved_places: int
    total_brukte: int
    total_ubrukte: int
    total_kost_brukte: float
    total_kost_ubrukte: float
    total_kostnad: float
    ssb_data: Optional[Dict] = None
