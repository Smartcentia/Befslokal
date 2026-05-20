import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, get_current_active_superuser
from app.domains.core.models.user import User
from app.services.intelligence.ki_kollega.service import ki_kollega_service, ChatContext

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str

# ... existing endpoints ...

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Create context for the service
        context_data = request.context or {}
        chat_context = ChatContext(
            page=context_data.get("path"),
            user_id=str(current_user.user_id) if current_user else None
        )
        
        # Determine prompt and history
        prompt = request.messages[-1]["content"] if request.messages else ""
        history = request.messages[:-1]
        
        # Execute analysis using the unified KI Kollega service
        # This gives the Analysis page full access to SQL and data tools
        result = await ki_kollega_service.chat_unified(
            message=prompt,
            context=chat_context,
            history=history,
            db=db,
            user=current_user
        )
        
        return {"response": result.get("answer", "Ingen svar generert fra AI-tjenesten.")}
    except Exception as e:
        logger.exception("Error in chat endpoint")
        return {"response": f"En feil oppstod under analysen: {str(e)}. Vennligst prøv igjen senere eller bruk KI-Kollega direkte."}
@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time dashboard statistics.
    """
    try:
        # Try DB first using raw SQL for safety
        prop_count_result = await db.execute(text("SELECT COUNT(*) FROM properties"))
        prop_count = prop_count_result.scalar()

        contract_count_result = await db.execute(text("SELECT COUNT(*) FROM contracts"))
        contract_count = contract_count_result.scalar()
        
    # Risk stats from analysis/deviations (using real-time counts)
        # Assuming RiskAssessment table or deviations count
        risk_count = 0 
        
        return {
            "properties": prop_count,
            "contracts": contract_count,
            "risks": risk_count 
        }
    except Exception as e:
        logger.warning("Database unavailable or error: %s", e)
        # Return 0s if database is not available
        return {
            "properties": 0,
            "contracts": 0,
            "risks": 0
        }

from sqlalchemy import text
from app.domains.core.routers.properties import get_property as properties_get_property
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID

@router.get("/properties/{prop_id}")
async def get_property_detail(
    prop_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get property details by ID."""
    from app.domains.core.models.property import Property
    try:
        uuid_obj = UUID(prop_id)
        query = select(Property).filter(Property.property_id == uuid_obj)
        result = await db.execute(query)
        prop = result.scalar_one_or_none()
        if not prop:
             raise HTTPException(status_code=404, detail="Eiendom ikke funnet")
        return prop
    except ValueError:
         raise HTTPException(status_code=400, detail="Ugyldig ID format")

@router.get("/contracts/{contract_id}")
async def get_contract_detail(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contract details by ID."""
    from app.domains.core.models.contract import Contract
    try:
        uuid_obj = UUID(contract_id)
        query = select(Contract).filter(Contract.contract_id == uuid_obj)
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=404, detail="Kontrakt ikke funnet")
        return contract
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig ID format")

from app.services.external.brreg_service import BrregService

@router.get("/parties/{party_id}")
async def get_party_detail(
    party_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get party details by ID (Real BRRG)."""
    
    # Try BRRG first if it looks like an OrgNr
    if party_id.isdigit() and len(party_id) == 9:
        # Use PartyService to fetch AND persist data
        from app.domains.core.services.party_service import PartyService
        real_data = await PartyService.fetch_and_store_party(party_id, db)
        if real_data:
            return real_data
            
    # If not found or not orgnr
    raise HTTPException(status_code=404, detail="Part ikke funnet")

from app.services.proximity.service import ProximityService

@router.get("/properties/{prop_id}/proximity-services")
async def get_proximity_services(
    prop_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent nærliggende tjenester for eiendom via Mapbox."""
    from uuid import UUID
    from app.domains.core.models.property import Property
    result = await db.execute(select(Property).where(Property.property_id == UUID(prop_id)))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")
    if not prop.latitude or not prop.longitude:
        raise HTTPException(status_code=400, detail="Eiendom mangler koordinater")
    service = ProximityService(db)
    results = await service.fetch_proximity_services(
        prop.property_id, prop.latitude, prop.longitude
    )
    return {"services": [{"name": s.service_name, "type": s.service_type, "distance_meters": s.distance_meters} for s in results]}

from app.domains.hms.services.risk_service import RiskService

@router.post("/properties/{prop_id}/risk-assessment")
async def calculate_property_risk(
    prop_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculates risk based on Proximity (Map Data) and Internal Control.
    """
    risk = await RiskService.calculate_risk_for_property(prop_id, db)
    if not risk:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet or could not calculate risk")
    return risk

@router.post("/admin/batch-risk-update")
async def batch_risk_update(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_active_superuser),
):
    """
    Triggers batch update for all properties SYNCHRONOUSLY.
    """
    try:
        # Run directly in the request context
        result = await RiskService.batch_update_risks(db)
        return result
    except Exception as e:
        logger.exception("Batch Update Failed")
        raise HTTPException(status_code=500, detail=str(e))



# ---------------------------------------------------------
# Internal Control Process Engine & Pedagogical AI
# ---------------------------------------------------------
from app.domains.hms.services.process_service import ProcessService
from app.domains.hms.services.pedagogical_service import PedagogicalService
from pydantic import BaseModel

class ProcessTransitionRequest(BaseModel):
    action: str
    data: Dict[str, Any] = {}

class PedagogueRequest(BaseModel):
    step: str
    context: str = ""

@router.get("/processes/{deviation_id}")
async def get_process(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ProcessService.get_process(deviation_id, db)

@router.post("/processes/{deviation_id}/next")
async def transition_process(
    deviation_id: str,
    request: ProcessTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ProcessService.transition(deviation_id, request.action, request.data, db)

@router.post("/processes/ai-help")
async def get_pedagogical_help(
    request: PedagogueRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get context-aware help from the Pedagogical AI.
    """
    return {"guidance": await PedagogicalService.get_guidance(request.context, request.step)}

# Removed old chat endpoint v
