from fastapi import APIRouter, HTTPException
from app.domains.hms.services.risk_service import risk_service
from pydantic import BaseModel

router = APIRouter()

class RiskRequest(BaseModel):
    property_id: str

@router.get("/")
async def root():
    return {"status": "Risk/Security MCP Server Active"}

from app.api.deps import get_current_user
from fastapi import APIRouter, HTTPException, Depends

@router.post("/classify", dependencies=[Depends(get_current_user)])
async def classify_risk(request: RiskRequest):
    """
    Classify the risk of a property.
    """
    try:
        # Fixed: Usage of correct method name from risk_service
        result = await risk_service.calculate_risk_for_property(request.property_id)
        if not result:
             raise HTTPException(status_code=404, detail="Property not found")
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
