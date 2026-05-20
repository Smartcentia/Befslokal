from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.domains.hms.models.checklist import ChecklistTemplate, ChecklistExecution
from app.domains.core.models.user import User

from app.schemas.checklist import (
    ChecklistTemplate as ChecklistTemplateSchema,
    ChecklistTemplateCreate,
    ChecklistTemplateUpdate,
)

router = APIRouter()


def _serialize_template(t: ChecklistTemplate) -> dict:
    return {
        "template_id": str(t.template_id),
        "title": t.title,
        "description": t.description,
        "items": t.items,
        "category": t.category,
        "frequency": t.frequency,
        "created_by_user_id": str(t.created_by_user_id) if t.created_by_user_id else None,
        "scope": t.scope or "system",
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/templates")
async def get_templates(
    scope: Optional[str] = Query(None, description="my|shared|all - filtrer maler"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent sjekklistemaler. scope=my: kun egne, shared: delte/system, all: alle.
    """
    query = select(ChecklistTemplate)
    if scope == "my":
        query = query.where(ChecklistTemplate.created_by_user_id == current_user.user_id)
    elif scope == "shared":
        query = query.where(
            or_(
                ChecklistTemplate.scope.in_(["system", "region", "global"]),
                ChecklistTemplate.scope.is_(None),
            )
        )
    # scope=all eller ingen: returner alle
    result = await db.execute(query)
    templates = result.scalars().all()
    return [_serialize_template(t) for t in templates]


@router.post("/templates")
async def create_template(
    body: ChecklistTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opprett brukerdefinert sjekklistemal (scope=user)."""
    template = ChecklistTemplate(
        title=body.title,
        description=body.description,
        items=body.items,
        category=body.category,
        frequency=body.frequency,
        created_by_user_id=current_user.user_id,
        scope="user",
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return _serialize_template(template)


@router.put("/templates/{template_id}")
async def update_template(
    template_id: UUID,
    body: ChecklistTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Oppdater mal (kun eier)."""
    result = await db.execute(
        select(ChecklistTemplate).where(ChecklistTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.created_by_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can update this template",
        )
    if body.title is not None:
        template.title = body.title
    if body.description is not None:
        template.description = body.description
    if body.items is not None:
        template.items = body.items
    if body.category is not None:
        template.category = body.category
    if body.frequency is not None:
        template.frequency = body.frequency
    await db.commit()
    await db.refresh(template)
    return _serialize_template(template)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Slett mal (kun eier)."""
    result = await db.execute(
        select(ChecklistTemplate).where(ChecklistTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.created_by_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete this template",
        )
    await db.delete(template)
    await db.commit()
    return {"message": "Template deleted"}


@router.post("/executions")
async def create_execution(
    template_id: str, 
    property_id: str, 
    user_id: str, # In real app, get from current_user
    db: AsyncSession = Depends(get_db)
):
    execution = ChecklistExecution(
        template_id=UUID(template_id),
        property_id=UUID(property_id),
        user_id=UUID(user_id)
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution

@router.get("/executions/{property_id}")
async def get_executions(property_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChecklistExecution).where(ChecklistExecution.property_id == UUID(property_id)))
    return result.scalars().all()
