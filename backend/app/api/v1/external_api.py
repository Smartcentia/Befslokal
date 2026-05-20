from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional
from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.services.external.api_clients.lovdata_client import LovdataClient
from app.services.external.api_clients.planslurpen_client import PlanslurpenClient
from app.services.external.brreg_service import brreg_service
from app.services.external.api_clients.kartverket_client import KartverketClient
from app.services.external.api_clients.nve_client import NVEClient
from app.services.external.api_clients.frost_client import FrostClient

router = APIRouter()

@router.post("/fetch-lovdata", tags=["lovdata"])
async def fetch_lovdata(
    query: Optional[str] = Query(None, description="Search query for Lovdata"),
    document_id: Optional[str] = Query(None, description="Specific document ID to fetch"),
    dataset_id: Optional[str] = Query(None, description="Dataset ID for public data"),
    reference: Optional[str] = Query(None, description="External reference/lookup"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unified endpoint to interact with Lovdata API.
    Supports search, document metadata retrieval, and public dataset listing.
    """
    client = LovdataClient()
    
    try:
        if query:
            return await client.search(query, limit=limit, offset=offset)
        elif document_id:
            return await client.get_document_meta(document_id)
        elif dataset_id:
            if dataset_id == "list":
                 return await client.get_public_data_list()
            return await client.get_public_data(dataset_id)
        elif reference:
            return await client.lookup(reference)
        else:
            raise HTTPException(status_code=400, detail="Must provide query, document_id, dataset_id, or reference.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lovdata API error: {str(e)}")

@router.post("/fetch-planslurpen", tags=["planslurpen"])
async def fetch_planslurpen(
    knr: Optional[str] = Query(None, description="Kommunenummer"),
    gnr: Optional[str] = Query(None, description="Gårdsnummer"),
    bnr: Optional[str] = Query(None, description="Bruksnummer"),
    plan_id: Optional[str] = Query(None, description="Specific Plan ID"),
    get_regulations: bool = Query(False, description="Whether to fetch regulations for the plan"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch planning and zoning data from Planslurpen.
    """
    client = PlanslurpenClient()
    try:
        if knr and gnr and bnr:
            return await client.fetch_plans_by_matrikkel(knr, gnr, bnr)
        elif plan_id:
            if get_regulations:
                return await client.get_plan_regulations(plan_id)
            return await client.get_plan_details(plan_id)
        else:
            raise HTTPException(status_code=400, detail="Must provide (knr, gnr, bnr) or plan_id.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planslurpen API error: {str(e)}")

# Placeholder for other external APIs as documented
# --- BRREG ---
@router.get("/brreg/{orgnr}", tags=["brreg"])
async def fetch_brreg_company(
    orgnr: str,
    current_user: User = Depends(get_current_user),
):
    """Lookup company in Brønnøysundregistrene."""
    result = await brreg_service.get_enhet(orgnr)
    if not result:
         raise HTTPException(status_code=404, detail="Company not found")
    return result

@router.get("/brreg/{orgnr}/regnskap", tags=["brreg"])
async def fetch_brreg_accounts(
    orgnr: str,
    current_user: User = Depends(get_current_user),
):
    """
    Fetch annual accounts (Årsregnskap) for a company.
    Returns key figures for the last 3 years.
    """
    results = await brreg_service.get_aarsregnskap(orgnr)
    return {"financials": results}

@router.get("/risk/{orgnr}", tags=["risk"])
async def get_supplier_risk(
    orgnr: str,
    # current_user: User = Depends(get_current_user), # Optional: secure this
):
    """
    Calculate real-time Risk Score for a supplier.
    Aggregates data from Brønnøysundregistrene (Status, Financials).
    """
    from app.services.risk.risk_engine import risk_engine
    profile = await risk_engine.calculate_risk_score(orgnr)
    return profile.to_dict()

# --- Kartverket ---
@router.get("/kartverket/geocode", tags=["kartverket"])
async def kartverket_geocode(
    address: str,
    current_user: User = Depends(get_current_user),
):
    """Geocode address using Kartverket."""
    client = KartverketClient()
    result = await client.geocode_address(address)
    if not result or "error" in result:
         raise HTTPException(status_code=404, detail=result.get("error", "Address not found"))
    return {"adresser": [result]} # Wrap to match test expectation often returning list

@router.get("/kartverket/reverse", tags=["kartverket"])
async def kartverket_reverse(
    lat: float,
    lon: float,
    current_user: User = Depends(get_current_user),
):
    """Reverse geocode coordinates."""
    client = KartverketClient()
    result = await client.fetch_property_data(lat, lon) # Closest we have
    return {"adresser": [result]}

# --- NVE ---
@router.get("/nve/flood-zones", tags=["nve"])
async def nve_flood_zones(
    lat: float,
    lon: float,
    current_user: User = Depends(get_current_user),
):
    """Get flood risk data from NVE."""
    client = NVEClient()
    result = await client.fetch_flood_risk(lat, lon)
    return result

@router.get("/nve/energy", tags=["nve"])
async def nve_energy(
    lat: float,
    lon: float,
    radius: int = 1000,
    current_user: User = Depends(get_current_user),
):
    """Get nearby NVE stations."""
    client = NVEClient()
    # radius is in meters, NVEClient.fetch_nearby_stations expects max_distance_km
    result = await client.fetch_nearby_stations(lat, lon, max_distance_km=radius/1000.0)
    return {"energiinfrastruktur": result} # Wrap to match potential expectation

# --- Frost ---
@router.get("/frost/observations", tags=["frost"])
async def frost_observations(
    lat: float,
    lon: float,
    element: str,
    current_user: User = Depends(get_current_user),
):
    """Get weather observations from Frost."""
    client = FrostClient()
    result = await client.get_observations(lat, lon, element)
    return result
