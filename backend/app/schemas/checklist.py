from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

class ChecklistTemplateBase(BaseModel):
    title: str
    description: Optional[str] = None
    items: List[Dict]
    category: str
    frequency: Optional[str] = None

class ChecklistTemplateCreate(ChecklistTemplateBase):
    pass

class ChecklistTemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[Dict]] = None
    category: Optional[str] = None
    frequency: Optional[str] = None

class ChecklistTemplate(ChecklistTemplateBase):
    template_id: UUID
    created_by_user_id: Optional[UUID] = None
    scope: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChecklistExecutionBase(BaseModel):
    template_id: UUID
    property_id: UUID
    user_id: UUID
    status: str = "in_progress"
    responses: Dict = {}

class ChecklistExecutionCreate(ChecklistExecutionBase):
    pass

class ChecklistExecution(ChecklistExecutionBase):
    execution_id: UUID
    completed_at: Optional[datetime] = None
    created_at: datetime
    template: Optional[ChecklistTemplate] = None

    model_config = ConfigDict(from_attributes=True)
