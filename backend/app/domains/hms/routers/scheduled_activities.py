"""
Scheduled Activities API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import logging

from app.api.deps import get_current_user, get_db
from app.domains.core.models.user import User
from app.core.property_access import check_property_access
from app.domains.hms.models.scheduled_activity import ScheduledActivity, ActivityTemplate
from app.domains.hms.services.activity_generator import ActivityGenerator
from app.domains.hms.services.activity_scheduler import ActivityScheduler
from app.schemas.scheduled_activity import (
    ScheduledActivityResponse,
    ActivityGenerationStats,
    UpcomingActivitiesRequest,
    CustomActivityCreate,
    AdoptTemplateRequest,
    ActivityTemplateResponse,
    ActivityTemplateCreate,
    ActivityTemplateUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/custom", response_model=ScheduledActivityResponse)
async def create_custom_activity(
    body: CustomActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Opprett en manuell aktivitet for en eiendom.
    Krever skrivetilgang til eiendommen.
    """
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(body.property_id),
        require_write=True
    )

    from app.domains.hms.services.activity_generator import ActivityGenerator

    recurrence = body.recurrence_rule or {"frequency": "monthly", "interval": 1, "day_of_month": body.due_date.day}
    next_due = body.due_date

    activity = ScheduledActivity(
        property_id=body.property_id,
        title=body.title,
        description=body.description,
        activity_type="monthly",
        category=body.category,
        priority=body.priority,
        responsible_role="eiendomsansvarlig",
        recurrence_rule=recurrence,
        next_due_date=next_due,
        enabled=True,
        created_by=current_user.email or "user",
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


@router.post("/generate", response_model=ActivityGenerationStats)
async def generate_activities(
    property_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate scheduled activities for properties.
    If property_id is provided, generates for that property only.
    Otherwise, generates for all properties.
    
    Requires ADMIN or REGIONAL_MANAGER role.
    """
    from app.domains.core.models.user import UserRole
    
    # Accept both the enum and the string value of the role
    user_role_val = getattr(current_user.role, "value", current_user.role)
    if user_role_val not in [UserRole.ADMIN.value, UserRole.REGIONAL_MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to generate activities"
        )
    
    generator = ActivityGenerator()
    
    if property_id:
        activities = await generator.generate_activities_for_property(db, property_id)
        stats = {
            "total_properties": 1,
            "total_activities_generated": len(activities),
            "properties_with_activities": 1 if activities else 0
        }
    else:
        stats = await generator.generate_activities_for_all_properties(db)
    
    return stats


@router.get("/scheduled", response_model=List[ScheduledActivityResponse])
async def get_scheduled_activities(
    property_id: Optional[UUID] = None,
    category: Optional[str] = None,
    responsible_role: Optional[str] = None,
    enabled: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all scheduled activities with optional filtering.
    """
    query = select(ScheduledActivity).where(ScheduledActivity.enabled == enabled)
    
    if property_id:
        query = query.where(ScheduledActivity.property_id == property_id)
    
    if category:
        query = query.where(ScheduledActivity.category == category)
    
    if responsible_role:
        query = query.where(ScheduledActivity.responsible_role == responsible_role)
    
    # TODO: Add role-based filtering (users should only see their properties)
    
    result = await db.execute(query.order_by(ScheduledActivity.next_due_date))
    activities = result.scalars().all()
    
    return activities


@router.get("/scheduled/property/{property_id}", response_model=List[ScheduledActivityResponse])
async def get_property_activities(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all scheduled activities for a specific property.
    """
    # TODO: Check if user has access to this property
    
    result = await db.execute(
        select(ScheduledActivity)
        .where(ScheduledActivity.property_id == property_id)
        .where(ScheduledActivity.enabled == True)
        .order_by(ScheduledActivity.next_due_date)
    )
    activities = result.scalars().all()
    
    return activities


@router.get("/upcoming", response_model=List[ScheduledActivityResponse])
async def get_upcoming_activities(
    days_ahead: int = 7,
    property_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get activities due within the next N days.
    """
    scheduler = ActivityScheduler()
    
    # Convert UUID to string if needed
    prop_id_str = str(property_id) if property_id else None
    user_id_str = str(current_user.user_id)
    
    activities = await scheduler.get_upcoming_activities(
        db,
        days_ahead=days_ahead,
        property_id=prop_id_str,
        user_id=user_id_str
    )
    
    return activities


@router.post("/process-due")
async def process_due_activities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger processing of due activities.
    Creates InternalControlCase for overdue activities.
    
    Typically run by cron, but can be triggered manually by admins.
    """
    from app.domains.core.models.user import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manually trigger activity processing"
        )
    
    scheduler = ActivityScheduler()
    stats = await scheduler.process_due_activities(db)
    
    return stats


@router.get("/templates", response_model=List[ActivityTemplateResponse])
async def get_activity_templates(
    scope: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent tilgjengelige aktivitetsmaler (hub).
    Viser system-maler, felles-maler (community), og brukerens egne maler.
    """
    from sqlalchemy import or_

    # Base query: enabled templates
    query = select(ActivityTemplate).where(ActivityTemplate.enabled == True)

    # Filter logic:
    # 1. Scope "system" -> All can see
    # 2. Scope "community" -> All can see
    # 3. Scope "user" -> Only creator can see
    # 4. Scope "region" -> Region managers can see (simplified for now to just show user's own + system/community)

    # Construct filter condition
    filter_condition = or_(
        ActivityTemplate.scope == "system",
        ActivityTemplate.scope == "community",
        ActivityTemplate.created_by_user_id == current_user.user_id
    )

    if scope:
        # If specific scope requested, strictly filter by it (but still respect permission)
        if scope == "mine":
            query = query.where(ActivityTemplate.created_by_user_id == current_user.user_id)
        elif scope == "system":
            query = query.where(ActivityTemplate.scope == "system")
        elif scope == "community":
            query = query.where(ActivityTemplate.scope == "community")
    else:
        #Default: show all accessible
        query = query.where(filter_condition)

    query = query.order_by(ActivityTemplate.adoption_count.desc().nullslast())

    result = await db.execute(query)
    templates = result.scalars().all()
    return [
        ActivityTemplateResponse(
            template_id=t.template_id,
            title=t.title,
            description=t.description,
            category=t.category,
            priority=t.priority,
            activity_type=t.activity_type,
            scope=getattr(t, "scope", None) or "system",
            adoption_count=getattr(t, "adoption_count", 0) or 0,
            created_by_user_id=getattr(t, "created_by_user_id", None),
        )
        for t in templates
    ]


@router.post("/templates", response_model=ActivityTemplateResponse)
async def create_activity_template(
    body: ActivityTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Opprett en ny aktivitetsmal.
    """
    template = ActivityTemplate(
        title=body.title,
        description=body.description,
        category=body.category,
        priority=body.priority,
        activity_type=body.activity_type,
        recurrence_pattern=body.recurrence_pattern,
        responsible_role=body.responsible_role,
        property_tags_required=body.property_tags_required,
        property_tags_excluded=body.property_tags_excluded,
        enabled=True,
        scope=body.scope or "user",
        created_by_user_id=current_user.user_id,
        adoption_count=0
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ActivityTemplateResponse(
        template_id=template.template_id,
        title=template.title,
        description=template.description,
        category=template.category,
        priority=template.priority,
        activity_type=template.activity_type,
        scope=template.scope,
        adoption_count=0,
        created_by_user_id=template.created_by_user_id
    )


@router.put("/templates/{template_id}", response_model=ActivityTemplateResponse)
async def update_activity_template(
    template_id: UUID,
    body: ActivityTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Oppdater en aktivitetsmal.
    Kun eier kan oppdatere.
    """
    result = await db.execute(select(ActivityTemplate).where(ActivityTemplate.template_id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.created_by_user_id != current_user.user_id:
        # TODO: Allow admins to edit system templates?
        raise HTTPException(status_code=403, detail="Not authorized to edit this template")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    await db.commit()
    await db.refresh(template)

    return ActivityTemplateResponse(
        template_id=template.template_id,
        title=template.title,
        description=template.description,
        category=template.category,
        priority=template.priority,
        activity_type=template.activity_type,
        scope=template.scope,
        adoption_count=template.adoption_count,
        created_by_user_id=template.created_by_user_id
    )


@router.delete("/templates/{template_id}")
async def delete_activity_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Slett en aktivitetsmal.
    Kun eier kan slette (eller admin).
    """
    result = await db.execute(select(ActivityTemplate).where(ActivityTemplate.template_id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.created_by_user_id != current_user.user_id:
        # TODO: proper admin check
        raise HTTPException(status_code=403, detail="Not authorized to delete this template")

    # Hard delete allowed for templates? Or soft delete?
    # Doing soft delete via enabled=False to preserve history if used?
    # For now, let's do hard delete if no one adopted it, or soft delete if adopted.
    # checking adoption count is not enough as it might be used but count logic is new.
    # Safest is soft delete.
    template.enabled = False 
    await db.commit()

    return {"message": "Template deleted"}


@router.post("/templates/{template_id}/publish", response_model=ActivityTemplateResponse)
async def publish_activity_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publiser en mal til fellesskapet (community).
    """
    result = await db.execute(select(ActivityTemplate).where(ActivityTemplate.template_id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.created_by_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to publish this template")

    template.scope = "community"
    await db.commit()
    await db.refresh(template)

    return ActivityTemplateResponse(
        template_id=template.template_id,
        title=template.title,
        description=template.description,
        category=template.category,
        priority=template.priority,
        activity_type=template.activity_type,
        scope=template.scope,
        adoption_count=template.adoption_count,
        created_by_user_id=template.created_by_user_id
    )


@router.post("/templates/{template_id}/adopt", response_model=ScheduledActivityResponse)
async def adopt_template(
    template_id: UUID,
    body: AdoptTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adopter en aktivitetsmal for en eiendom.
    Oppretter ScheduledActivity fra malen.
    """
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(body.property_id),
        require_write=True
    )

    result = await db.execute(
        select(ActivityTemplate).where(ActivityTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    from datetime import datetime
    from app.domains.hms.services.activity_generator import ActivityGenerator

    next_due = ActivityGenerator.calculate_next_due_date(template.recurrence_pattern)

    activity = ScheduledActivity(
        property_id=body.property_id,
        title=template.title,
        description=template.description,
        activity_type=template.activity_type,
        category=template.category,
        priority=template.priority,
        responsible_role=template.responsible_role,
        recurrence_rule=template.recurrence_pattern,
        next_due_date=next_due,
        enabled=True,
        created_by=f"hub:{template_id}",
    )
    db.add(activity)

    if hasattr(template, "adoption_count") and template.adoption_count is not None:
        template.adoption_count = (template.adoption_count or 0) + 1
    else:
        template.adoption_count = 1

    await db.commit()
    await db.refresh(activity)
    return activity


@router.post("/scheduled/{activity_id}/publish-to-hub", response_model=ActivityTemplateResponse)
async def publish_to_hub(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publiser en ScheduledActivity som mal i hub.
    Krever ADMIN eller REGIONAL_MANAGER.
    """
    from app.domains.core.models.user import UserRole

    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to publish to hub"
        )

    result = await db.execute(
        select(ScheduledActivity).where(ScheduledActivity.activity_id == activity_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    template = ActivityTemplate(
        title=activity.title,
        description=activity.description,
        category=activity.category,
        priority=activity.priority,
        activity_type=activity.activity_type,
        recurrence_pattern=activity.recurrence_rule,
        responsible_role=activity.responsible_role,
        property_tags_required=activity.property_tags_required,
        property_tags_excluded=activity.property_tags_excluded,
        enabled=True,
        created_by_user_id=current_user.user_id,
        scope="user" if current_user.role == UserRole.REGIONAL_MANAGER else "region",
        adoption_count=0,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ActivityTemplateResponse(
        template_id=template.template_id,
        title=template.title,
        description=template.description,
        category=template.category,
        priority=template.priority,
        activity_type=template.activity_type,
        scope=template.scope,
        adoption_count=0,
    )


@router.post("/scheduled/{activity_id}/trigger", response_model=dict)
async def trigger_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manuelt start en planlagt aktivitet og opprett en aktiv sak.
    Fremskynder også neste forfallsdato for aktiviteten.
    """
    # Hent aktiviteten først for å sjekke tilgang
    result = await db.execute(
        select(ScheduledActivity).where(ScheduledActivity.activity_id == activity_id)
    )
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    # Sjekk tilgang til eiendommen
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(activity.property_id),
        require_write=True
    )
    
    scheduler = ActivityScheduler()
    case = await scheduler.trigger_specific_activity(db, activity_id)
    
    if not case:
        raise HTTPException(status_code=500, detail="Failed to create case from activity")
        
    return {
        "message": "Aktivitet startet",
        "case_id": str(case.case_id),
        "title": case.title
    }


@router.delete("/scheduled/{activity_id}")
async def disable_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable (soft delete) a scheduled activity.
    """
    from app.domains.core.models.user import UserRole
    
    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete activities"
        )
    
    result = await db.execute(
        select(ScheduledActivity).where(ScheduledActivity.activity_id == activity_id)
    )
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    activity.enabled = False
    await db.commit()
    
    return {"message": "Activity disabled successfully"}
