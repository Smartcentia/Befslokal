from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.gdpr_service import gdpr_service
from pydantic import BaseModel

router = APIRouter()

class TextPayload(BaseModel):
    text: str
    entity_type: str = "unknown"
    entity_id: str = "unknown"

class RequestCreate(BaseModel):
    user_id: str
    request_type: str
    details: dict = {}

@router.get("/")
async def root():
    return {"status": "GDPR Compliance MCP Server Active"}

@router.post("/detect", dependencies=[Depends(get_current_user)])
async def detect_pii(payload: TextPayload):
    """
    Agent Action: Scan text for sensitive data before processing/storing.
    """
    return await gdpr_service.detect_pii(payload.text)

@router.post("/anonymize")
async def anonymize(payload: TextPayload, db: Session = Depends(get_db)):
    """
    Agent Action: Redact PII from text.
    """
    try:
        clean_text = await gdpr_service.anonymize_text(db, payload.text, payload.entity_type, payload.entity_id)
        return {"original_length": len(payload.text), "cleaned_text": clean_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests")
async def create_request(req: RequestCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Log a User's GDPR request (e.g., 'Delete my data').
    """
    try:
        return await gdpr_service.create_request(db, req.user_id, req.request_type, req.details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
