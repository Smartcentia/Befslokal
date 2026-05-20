"""
Pydantic schemas for Scheduled Activities
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class ScheduledActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    activity_type: str
    category: str
    priority: str = "medium"
    responsible_role: str
    recurrence_rule: Dict[str, Any]
    next_due_date: datetime
    enabled: bool = True
    property_tags_required: Optional[List[str]] = None
    property_tags_excluded: Optional[List[str]] = None


class ScheduledActivityCreate(ScheduledActivityBase):
    property_id: UUID
    assigned_user_id: Optional[UUID] = None


class ScheduledActivityResponse(ScheduledActivityBase):
    activity_id: UUID
    property_id: UUID
    assigned_user_id: Optional[UUID] = None
    last_generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityGenerationStats(BaseModel):
    total_properties: int
    total_activities_generated: int
    properties_with_activities: int


class UpcomingActivitiesRequest(BaseModel):
    days_ahead: int = 7
    property_id: Optional[UUID] = None


class CustomActivityCreate(BaseModel):
    """Create a custom (manual) scheduled activity for a property."""
    property_id: UUID
    title: str
    description: Optional[str] = None
    due_date: datetime
    recurrence_rule: Optional[Dict[str, Any]] = None  # Default: monthly
    category: str = "hms"
    priority: str = "medium"


class AdoptTemplateRequest(BaseModel):
    """Adopt an activity template for a property."""
    property_id: UUID


class ActivityTemplateCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    activity_type: str
    recurrence_pattern: Dict[str, Any]
    responsible_role: str
    property_tags_required: Optional[List[str]] = None
    property_tags_excluded: Optional[List[str]] = None
    scope: Optional[str] = "user"


class ActivityTemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    activity_type: Optional[str] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None
    responsible_role: Optional[str] = None
    property_tags_required: Optional[List[str]] = None
    property_tags_excluded: Optional[List[str]] = None
    scope: Optional[str] = None
    enabled: Optional[bool] = None


class ActivityTemplateResponse(BaseModel):
    template_id: UUID
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    activity_type: str
    scope: Optional[str] = None
    adoption_count: int = 0
    created_by_user_id: Optional[UUID] = None

    class Config:
        from_attributes = True
