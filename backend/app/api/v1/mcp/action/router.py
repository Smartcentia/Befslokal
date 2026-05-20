from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.domains.fdv.services.action_service import action_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class WorkOrderCreate(BaseModel):
    property_id: str
    description: str
    priority: str = "medium"

class TaskCreate(BaseModel):
    title: str
    action_type: str
    payload: dict = {}
    order_id: Optional[str] = None

@router.get("/")
async def root():
    return {"status": "Action MCP Server Active"}

@router.post("/work-orders")
async def create_work_order(wo: WorkOrderCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Create a new work order.
    """
    try:
        result = await action_service.create_work_order(db, wo.property_id, wo.description, wo.priority)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Schedule a generic task.
    """
    try:
        result = await action_service.create_task(db, task.title, task.action_type, task.payload, task.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
