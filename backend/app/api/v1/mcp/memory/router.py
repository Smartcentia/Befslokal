from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.domains.innsikt.services.memory_service import memory_service
from pydantic import BaseModel

router = APIRouter()

class PreferenceUpdate(BaseModel):
    user_id: str
    updates: dict

@router.get("/")
async def root():
    return {"status": "Memory/Learning MCP Server Active"}

@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str, db: Session = Depends(get_db)):
    """
    Agent Action: Retrieve user preferences (e.g., to personalize response or action).
    """
    try:
        return await memory_service.get_user_preferences(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preferences")
async def update_preferences(pref: PreferenceUpdate, db: Session = Depends(get_db)):
    """
    Agent Action: Update user preferences (learn from user).
    """
    try:
        return await memory_service.update_user_preferences(db, pref.user_id, pref.updates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
