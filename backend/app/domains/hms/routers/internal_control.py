from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.db.session import SessionLocal
from app.domains.hms.services.internal_control_service import InternalControlService
from app.domains.hms.services.follow_up_service import FollowUpService
from app.schemas.internal_control import (
    InternalControlCase,
    Notification,
    InternalControlCaseUpdate,
    InternalControlCaseCompleteChecklist,
    CaseFromTemplateRequest,
    ActivityWheelSummary,
)
from app.api.deps import get_current_user, get_db
from app.domains.core.models.user import User, UserRole
from app.core.property_access import check_property_access

router = APIRouter()

@router.get("/summary", response_model=ActivityWheelSummary)
async def get_activity_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent oppsummering av aktiviteter for 'aktivitetshjulet'.
    """
    from app.core.property_access import get_user_accessible_property_ids
    accessible_property_ids = await get_user_accessible_property_ids(db, current_user)
    
    # ADMIN has accessible_property_ids = None (all access)
    summary = await InternalControlService.get_activity_wheel_summary(db, accessible_property_ids)
    return summary

@router.get("/cases", response_model=List[InternalControlCase])
async def get_cases(
    property_id: Optional[UUID] = Query(None),
    status: Optional[str] = None,
    priority: Optional[str] = Query(None, description="Filter by priority: critical, high, medium, low"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent internkontroll saker (filtrert basert på property access).
    """
    # If property_id is specified, check access
    if property_id:
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(property_id),
            require_write=False
        )
    
    # Get cases
    all_cases = await InternalControlService.get_property_cases(db, property_id, status, priority)
    
    # If no property_id filter, filter cases based on property access
    if not property_id:
        from app.core.property_access import get_user_accessible_property_ids
        accessible_property_ids = await get_user_accessible_property_ids(db, current_user)
        
        if accessible_property_ids is None:
            # ADMIN - return all cases
            return all_cases
        elif len(accessible_property_ids) == 0:
            # No access
            return []
        else:
            # Filter cases to only those for accessible properties
            return [c for c in all_cases if c.property_id and UUID(c.property_id) in accessible_property_ids]
    
    return all_cases

@router.get("/cases/{case_id}", response_model=InternalControlCase)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent spesifikk internkontroll sak (med property access check).
    """
    case = await InternalControlService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Check property access
    if case.property_id:
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(case.property_id),
            require_write=False
        )
    
    return case


@router.patch("/cases/{case_id}", response_model=InternalControlCase)
async def update_case(
    case_id: UUID,
    body: InternalControlCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Oppdater internkontroll sak (status, notes, etc.).
    """
    case = await InternalControlService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(case.property_id),
        require_write=True
    )

    if body.title is not None:
        case.title = body.title
    if body.description is not None:
        case.description = body.description
    if body.status is not None:
        case.status = body.status
    if body.notes is not None:
        case.notes = body.notes
    if body.assigned_user_id is not None:
        case.assigned_user_id = str(body.assigned_user_id)
    if body.status == "closed":
        from datetime import datetime
        case.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(case)
    return case


@router.post("/cases/{case_id}/complete-checklist", response_model=InternalControlCase)
async def complete_checklist(
    case_id: UUID,
    body: InternalControlCaseCompleteChecklist,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fullfør sjekkliste på en internkontroll sak.
    Lagrer svar, setter status=closed.
    """
    case = await InternalControlService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(case.property_id),
        require_write=True
    )

    result = await InternalControlService.complete_checklist(
        db=db,
        case_id=case_id,
        user_id=current_user.user_id,
        responses=body.responses,
        notes=body.notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    return result


@router.post("/cases/from-template", response_model=InternalControlCase)
async def create_case_from_template(
    body: CaseFromTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Opprett internkontroll sak fra en ChecklistTemplate.
    Krever skrivetilgang til eiendommen.
    """
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(body.property_id),
        require_write=True,
    )
    case = await InternalControlService.create_case_from_template(
        db=db,
        template_id=body.template_id,
        property_id=body.property_id,
        assigned_user_id=current_user.user_id,
    )
    if not case:
        raise HTTPException(status_code=404, detail="Template or property not found")
    return case


@router.post("/cases/create-initial-for-property/{property_id}")
async def create_initial_cases(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Opprett initiale internkontroll saker for en property (med property access check).
    """
    # Check property access (write access required to create cases)
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(property_id),
        require_write=True
    )
    
    # Use real logged in user ID
    user_id = current_user.user_id
    return await InternalControlService.create_initial_cases_for_property(db, property_id, assigned_user_id=user_id)

@router.get("/notifications", response_model=List[Notification])
async def get_notifications(unread_only: bool = False, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.user_id
    return await InternalControlService.get_user_notifications(db, user_id, unread_only)

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.user_id
    return await InternalControlService.mark_notification_as_read(db, notification_id, user_id)


class SendMessageRequest(BaseModel):
    to_email: str           # mottakers e-post
    title: str
    message: str


@router.post("/messages/send", status_code=201)
async def send_internal_message(
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send en intern melding til en annen bruker.
    Oppretter en Notification hos mottakeren med type='message'.
    """
    from app.domains.core.models.user import User as UserModel
    from app.domains.hms.models.internal_control import Notification as NotificationModel
    from sqlalchemy import select as sa_select

    # Finn mottaker
    res = await db.execute(
        sa_select(UserModel).where(UserModel.email == body.to_email)
    )
    recipient = res.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Bruker '{body.to_email}' finnes ikke")

    sender_name = current_user.full_name or current_user.email or "Ukjent"
    notif = NotificationModel(
        user_id=recipient.user_id,
        title=body.title,
        message=f"Fra {sender_name}: {body.message}",
        notification_type="message",
    )
    db.add(notif)
    await db.commit()
    return {"sent": True, "to": body.to_email}


@router.get("/users/list")
async def list_users_for_messaging(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returnerer liste over brukere som kan motta meldinger."""
    from app.domains.core.models.user import User as UserModel
    from sqlalchemy import select as sa_select

    res = await db.execute(
        sa_select(UserModel.user_id, UserModel.email, UserModel.full_name)
        .order_by(UserModel.full_name)
    )
    return [
        {"user_id": str(r.user_id), "email": r.email, "name": r.full_name or r.email}
        for r in res.all()
        if r.email != current_user.email
    ]


@router.post("/process-overdue")
async def process_overdue_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Prosesser forfalte internkontroll-saker. Sender purringer og eskalerer.
    Kun ADMIN kan kjøre manuelt. Typisk kjøres daglig via cron.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can trigger overdue processing"
        )
    stats = await FollowUpService.process_overdue_cases(db)
    return stats


@router.post("/generate-initial-cases")
async def generate_initial_cases_bulk(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates sample RKL 6 cases for ALL properties in the system (kun ADMIN).
    """
    # Kun ADMIN kan generere cases for alle properties
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can generate cases for all properties"
        )
    
    from app.domains.core.models.property import Property
    from sqlalchemy import select
    from app.core.property_access import filter_properties_by_access
    
    # Get all properties
    result = await db.execute(select(Property))
    all_properties = result.scalars().all()
    
    # Filter based on user access (for ADMIN this will return all)
    accessible_properties = await filter_properties_by_access(
        db=db,
        user=current_user,
        properties=list(all_properties)
    )
    
    total_created = 0
    # Use real user
    user_id = current_user.user_id
    
    for prop in accessible_properties:
        # Generate cases for this property
        cases = await InternalControlService.create_initial_cases_for_property(db, prop.property_id, assigned_user_id=user_id)
        total_created += len(cases)
        
    return {"message": f"Generated {total_created} cases for {len(accessible_properties)} properties using Admin: {current_user.email}"}
