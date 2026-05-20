from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from app.schemas.property import Property
from app.schemas.user import UserMinimal

# --- Cases ---

class InternalControlCaseCompleteChecklist(BaseModel):
    """Request body for completing a checklist on an internal control case."""
    responses: Dict[str, bool]  # {"0": true, "1": false} - index -> checked
    notes: Optional[str] = None


class CaseFromTemplateRequest(BaseModel):
    """Request body for creating an InternalControlCase from a ChecklistTemplate."""
    template_id: UUID
    property_id: UUID

class InternalControlCaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    case_type: str
    priority: str = "medium"
    due_date: Optional[datetime] = None
    assigned_user_id: Optional[UUID] = None

class InternalControlCaseCreate(InternalControlCaseBase):
    property_id: UUID

class InternalControlCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_user_id: Optional[UUID] = None

class InternalControlCase(InternalControlCaseBase):
    case_id: UUID
    property_id: UUID
    property: Optional[Property] = None
    assigned_user: Optional[UserMinimal] = None
    status: str
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    process_data: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Notifications ---

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None

class NotificationCreate(NotificationBase):
    user_id: UUID

class Notification(NotificationBase):
    notification_id: UUID
    user_id: UUID
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Activity Wheel ---

class ActivityStatusSummary(BaseModel):
    status: str
    count: int

class ActivityWheelItem(BaseModel):
    name: str  # Category or Type
    total: int
    completed: int
    open: int
    overdue: int

class ActivityWheelSummary(BaseModel):
    items: List[ActivityWheelItem]
    total_cases: int
