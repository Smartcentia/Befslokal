from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.domains.fdv.services.bim_service import bim_service
from pydantic import BaseModel

router = APIRouter()

class ModelUpload(BaseModel):
    property_id: str
    filename: str

class SpatialQuery(BaseModel):
    model_id: str
    x: float
    y: float
    radius: float = 5.0

@router.get("/")
async def root():
    return {"status": "BIM/IFC MCP Server Active"}

@router.post("/upload")
async def upload_model(upload: ModelUpload, db: Session = Depends(get_db)):
    """
    Agent Action: Upload a BIM/IFC file for parsing.
    """
    try:
        return await bim_service.upload_model(db, upload.property_id, upload.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_objects(query: SpatialQuery, db: Session = Depends(get_db)):
    """
    Agent Action: Find objects near a specific 3D coordinate.
    """
    try:
        return await bim_service.get_objects_near(db, query.model_id, query.x, query.y, query.radius)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
