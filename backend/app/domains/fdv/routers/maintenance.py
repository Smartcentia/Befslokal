"""
Vedlikeholdsplan – MaintenancePlan & MaintenanceTask

Endepunkter:
  GET    /fdvu/maintenance/plans?property_id=
  POST   /fdvu/maintenance/plans
  PATCH  /fdvu/maintenance/plans/{plan_id}
  DELETE /fdvu/maintenance/plans/{plan_id}
  POST   /fdvu/maintenance/plans/{plan_id}/generate-tasks   – generer kommende oppgaver
  GET    /fdvu/maintenance/tasks?property_id=&status=
  PATCH  /fdvu/maintenance/tasks/{task_id}                  – oppdater status/fullføring
  GET    /fdvu/maintenance/summary/{property_id}            – KPI-oversikt
"""
import uuid
from datetime import date, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.fdv.models.maintenance import MaintenancePlan, MaintenanceTask

router = APIRouter()

# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class PlanCreate(BaseModel):
    property_id: uuid.UUID
    component_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    category: str = "preventive"          # preventive|inspection|cleaning|corrective|legal
    frequency_months: int = 12
    responsible_role: str = "janitor"     # janitor|contractor|property_manager
    estimated_cost_nok: Optional[Decimal] = None
    ns3451_code: Optional[str] = None
    last_performed_date: Optional[date] = None

class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    frequency_months: Optional[int] = None
    responsible_role: Optional[str] = None
    estimated_cost_nok: Optional[Decimal] = None
    ns3451_code: Optional[str] = None
    last_performed_date: Optional[date] = None
    is_active: Optional[bool] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    completion_notes: Optional[str] = None
    actual_cost_nok: Optional[Decimal] = None
    assigned_to_user_id: Optional[uuid.UUID] = None

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _compute_next_due(last: Optional[date], freq_months: int) -> date:
    """Beregn neste forfallsdato basert på siste utførelse + frekvens."""
    base = last or date.today()
    # Legg til måneder (forenklet: antall måneder * 30 dager)
    days = freq_months * 30
    return base + timedelta(days=days)

def _plan_to_dict(p: MaintenancePlan) -> dict:
    return {
        "plan_id": str(p.plan_id),
        "property_id": str(p.property_id),
        "component_id": str(p.component_id) if p.component_id else None,
        "title": p.title,
        "description": p.description,
        "category": p.category,
        "frequency_months": p.frequency_months,
        "responsible_role": p.responsible_role,
        "estimated_cost_nok": float(p.estimated_cost_nok) if p.estimated_cost_nok else None,
        "ns3451_code": p.ns3451_code,
        "last_performed_date": p.last_performed_date.isoformat() if p.last_performed_date else None,
        "next_due_date": p.next_due_date.isoformat() if p.next_due_date else None,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }

def _task_to_dict(t: MaintenanceTask) -> dict:
    return {
        "task_id": str(t.task_id),
        "plan_id": str(t.plan_id),
        "property_id": str(t.property_id),
        "component_id": str(t.component_id) if t.component_id else None,
        "title": t.title,
        "description": t.description,
        "due_date": t.due_date.isoformat(),
        "status": t.status,
        "assigned_to_user_id": str(t.assigned_to_user_id) if t.assigned_to_user_id else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "completion_notes": t.completion_notes,
        "actual_cost_nok": float(t.actual_cost_nok) if t.actual_cost_nok else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }

# ─────────────────────────────────────────────
# Plans
# ─────────────────────────────────────────────

@router.get("/maintenance/plans", tags=["Vedlikeholdsplan"])
async def get_plans(
    property_id: uuid.UUID = Query(...),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conditions = [MaintenancePlan.property_id == property_id]
    if active_only:
        conditions.append(MaintenancePlan.is_active == True)  # noqa: E712
    rows = await db.execute(select(MaintenancePlan).where(and_(*conditions)).order_by(MaintenancePlan.next_due_date))
    return [_plan_to_dict(p) for p in rows.scalars().all()]


@router.post("/maintenance/plans", status_code=201, tags=["Vedlikeholdsplan"])
async def create_plan(
    body: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    next_due = _compute_next_due(body.last_performed_date, body.frequency_months)
    plan = MaintenancePlan(
        plan_id=uuid.uuid4(),
        property_id=body.property_id,
        component_id=body.component_id,
        title=body.title,
        description=body.description,
        category=body.category,
        frequency_months=body.frequency_months,
        responsible_role=body.responsible_role,
        estimated_cost_nok=body.estimated_cost_nok,
        ns3451_code=body.ns3451_code,
        last_performed_date=body.last_performed_date,
        next_due_date=next_due,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _plan_to_dict(plan)


@router.patch("/maintenance/plans/{plan_id}", tags=["Vedlikeholdsplan"])
async def update_plan(
    plan_id: uuid.UUID,
    body: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = await db.execute(select(MaintenancePlan).where(MaintenancePlan.plan_id == plan_id))
    plan = row.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan ikke funnet")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(plan, field, val)

    # Recalculate next_due if relevant fields changed
    if body.last_performed_date is not None or body.frequency_months is not None:
        plan.next_due_date = _compute_next_due(plan.last_performed_date, plan.frequency_months)

    await db.commit()
    await db.refresh(plan)
    return _plan_to_dict(plan)


@router.delete("/maintenance/plans/{plan_id}", status_code=204, tags=["Vedlikeholdsplan"])
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = await db.execute(select(MaintenancePlan).where(MaintenancePlan.plan_id == plan_id))
    plan = row.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan ikke funnet")
    await db.delete(plan)
    await db.commit()

# ─────────────────────────────────────────────
# Generate tasks from a plan
# ─────────────────────────────────────────────

@router.post("/maintenance/plans/{plan_id}/generate-tasks", tags=["Vedlikeholdsplan"])
async def generate_tasks(
    plan_id: uuid.UUID,
    horizon_months: int = Query(12, ge=1, le=36, description="Generer oppgaver for N måneder fremover"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Generer kommende MaintenanceTask-er for planen, unngå duplikater."""
    row = await db.execute(select(MaintenancePlan).where(MaintenancePlan.plan_id == plan_id))
    plan = row.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan ikke funnet")

    today = date.today()
    horizon_end = today + timedelta(days=horizon_months * 30)

    # Finn alle eksisterende due_dates for denne planen
    existing = await db.execute(
        select(MaintenanceTask.due_date).where(MaintenanceTask.plan_id == plan_id)
    )
    existing_dates = {r[0] for r in existing.fetchall()}

    created = 0
    current = plan.next_due_date or today
    while current <= horizon_end:
        if current not in existing_dates:
            db.add(MaintenanceTask(
                task_id=uuid.uuid4(),
                plan_id=plan.plan_id,
                property_id=plan.property_id,
                component_id=plan.component_id,
                title=plan.title,
                description=plan.description,
                due_date=current,
                status="overdue" if current < today else "pending",
            ))
            created += 1
        current += timedelta(days=plan.frequency_months * 30)

    await db.commit()
    return {"created": created, "plan_id": str(plan_id), "horizon_months": horizon_months}

# ─────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────

@router.get("/maintenance/tasks", tags=["Vedlikeholdsplan"])
async def get_tasks(
    property_id: uuid.UUID = Query(...),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conditions = [MaintenanceTask.property_id == property_id]
    if status:
        conditions.append(MaintenanceTask.status == status)
    rows = await db.execute(
        select(MaintenanceTask).where(and_(*conditions)).order_by(MaintenanceTask.due_date)
    )
    return [_task_to_dict(t) for t in rows.scalars().all()]


@router.patch("/maintenance/tasks/{task_id}", tags=["Vedlikeholdsplan"])
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import datetime, timezone
    row = await db.execute(select(MaintenanceTask).where(MaintenanceTask.task_id == task_id))
    task = row.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Oppgave ikke funnet")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(task, field, val)

    if body.status == "completed" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
        # Oppdater plan.last_performed_date + next_due_date
        plan_row = await db.execute(select(MaintenancePlan).where(MaintenancePlan.plan_id == task.plan_id))
        plan = plan_row.scalar_one_or_none()
        if plan:
            plan.last_performed_date = task.due_date
            plan.next_due_date = _compute_next_due(task.due_date, plan.frequency_months)

    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)

# ─────────────────────────────────────────────
# BIM-kobling
# ─────────────────────────────────────────────

# IFC-typer som regnes som driftsrelevant utstyr
_EQUIPMENT_TYPES = {
    "IfcBoiler", "IfcChiller", "IfcPump", "IfcUnitaryEquipment",
    "IfcFlowTerminal", "IfcAirTerminal", "IfcElectricAppliance",
    "IfcLightFixture", "IfcFireSuppressionTerminal", "IfcSanitaryTerminal",
    "IfcCoolingTower", "IfcHeatExchanger",
}


class BIMQuickCreate(BaseModel):
    title: str
    category: str = "preventive"
    frequency_months: int = 12
    responsible_role: str = "contractor"
    estimated_cost_nok: Optional[Decimal] = None
    ns3451_code: Optional[str] = None


@router.get("/maintenance/bim/{property_id}/equipment", tags=["BIM-vedlikehold"])
async def get_bim_equipment(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Hent BIM-objekter av utstyrstyper for eiendommen.
    Viser om de er koblet til komponent og vedlikeholdsplan.
    """
    from app.domains.fdv.models.bim import BIMModel, BIMObject
    from app.domains.fdv.models.fdv import BuildingComponent

    # Finn alle BIMModel-IDer for eiendommen
    model_rows = await db.execute(
        select(BIMModel.model_id).where(BIMModel.property_id == property_id)
    )
    model_ids = [r[0] for r in model_rows.fetchall()]
    if not model_ids:
        return {"property_id": str(property_id), "equipment": []}

    # Hent utstyrsobjekter
    obj_rows = await db.execute(
        select(BIMObject).where(
            BIMObject.model_id.in_(model_ids),
            BIMObject.type.in_(_EQUIPMENT_TYPES),
        ).order_by(BIMObject.type, BIMObject.name)
    )
    objects = obj_rows.scalars().all()

    # Hent tilhørende komponenter + planer
    result = []
    for obj in objects:
        comp = None
        plans = []
        if obj.linked_component_id:
            comp_row = await db.get(BuildingComponent, obj.linked_component_id)
            comp = comp_row

            plan_rows = await db.execute(
                select(MaintenancePlan).where(
                    MaintenancePlan.component_id == obj.linked_component_id,
                    MaintenancePlan.is_active == True,  # noqa: E712
                )
            )
            plans = plan_rows.scalars().all()

        # Neste forfallsdato
        next_due = min((p.next_due_date for p in plans if p.next_due_date), default=None)
        overdue = next_due and next_due < date.today()

        result.append({
            "object_id":         str(obj.object_id),
            "ifc_guid":          obj.ifc_guid,
            "name":              obj.name or obj.type,
            "type":              obj.type,
            "pos_x":             obj.pos_x,
            "pos_y":             obj.pos_y,
            "pos_z":             obj.pos_z,
            "linked_component":  {
                "component_id": str(comp.component_id),
                "name":         comp.name,
                "status":       comp.status,
            } if comp else None,
            "plans_count":       len(plans),
            "next_due_date":     next_due.isoformat() if next_due else None,
            "is_overdue":        bool(overdue),
        })

    return {"property_id": str(property_id), "count": len(result), "equipment": result}


@router.post("/maintenance/bim/{object_id}/quick-create", status_code=201, tags=["BIM-vedlikehold"])
async def bim_quick_create_plan(
    object_id: uuid.UUID,
    body: BIMQuickCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Opprett BuildingComponent + MaintenancePlan direkte fra et BIM-objekt.
    Kobler BIMObject.linked_component_id til den nye komponenten.
    """
    from app.domains.fdv.models.bim import BIMModel, BIMObject
    from app.domains.fdv.models.fdv import BuildingComponent

    obj_row = await db.execute(select(BIMObject).where(BIMObject.object_id == object_id))
    obj = obj_row.scalar_one_or_none()
    if not obj:
        raise HTTPException(404, "BIM-objekt ikke funnet")

    # Finn property_id via BIMModel
    model_row = await db.get(BIMModel, obj.model_id)
    if not model_row:
        raise HTTPException(404, "BIMModel ikke funnet")
    property_id = model_row.property_id

    # Opprett komponent (eller gjenbruk eksisterende)
    if obj.linked_component_id:
        comp_id = obj.linked_component_id
    else:
        comp = BuildingComponent(
            component_id=uuid.uuid4(),
            property_id=property_id,
            name=obj.name or obj.type or "Ukjent komponent",
            type=obj.type,
            status="active",
            technical_data={"ifc_guid": obj.ifc_guid, "source": "IFC-import"},
        )
        db.add(comp)
        await db.flush()
        comp_id = comp.component_id
        obj.linked_component_id = comp_id

    # Opprett vedlikeholdsplan
    next_due = _compute_next_due(None, body.frequency_months)
    plan = MaintenancePlan(
        plan_id=uuid.uuid4(),
        property_id=property_id,
        component_id=comp_id,
        title=body.title,
        category=body.category,
        frequency_months=body.frequency_months,
        responsible_role=body.responsible_role,
        estimated_cost_nok=body.estimated_cost_nok,
        ns3451_code=body.ns3451_code,
        next_due_date=next_due,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {
        "plan_id":       str(plan.plan_id),
        "component_id":  str(comp_id),
        "object_id":     str(object_id),
        "next_due_date": plan.next_due_date.isoformat() if plan.next_due_date else None,
    }


# ─────────────────────────────────────────────
# Summary / KPI
# ─────────────────────────────────────────────

@router.get("/maintenance/summary/{property_id}", tags=["Vedlikeholdsplan"])
async def maintenance_summary(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = date.today()

    plans_count = await db.scalar(
        select(func.count()).where(
            and_(MaintenancePlan.property_id == property_id, MaintenancePlan.is_active == True)  # noqa: E712
        )
    )
    tasks_total = await db.scalar(
        select(func.count()).where(MaintenanceTask.property_id == property_id)
    )
    tasks_pending = await db.scalar(
        select(func.count()).where(
            and_(MaintenanceTask.property_id == property_id, MaintenanceTask.status == "pending")
        )
    )
    tasks_overdue = await db.scalar(
        select(func.count()).where(
            and_(
                MaintenanceTask.property_id == property_id,
                MaintenanceTask.status.in_(["pending", "overdue"]),
                MaintenanceTask.due_date < today,
            )
        )
    )
    tasks_completed = await db.scalar(
        select(func.count()).where(
            and_(MaintenanceTask.property_id == property_id, MaintenanceTask.status == "completed")
        )
    )
    # Neste forfallsdato
    next_due_row = await db.execute(
        select(MaintenancePlan.title, MaintenancePlan.next_due_date)
        .where(
            and_(
                MaintenancePlan.property_id == property_id,
                MaintenancePlan.is_active == True,  # noqa: E712
                MaintenancePlan.next_due_date >= today,
            )
        )
        .order_by(MaintenancePlan.next_due_date)
        .limit(1)
    )
    next_due = next_due_row.first()

    return {
        "property_id": str(property_id),
        "plans_active": plans_count or 0,
        "tasks_total": tasks_total or 0,
        "tasks_pending": tasks_pending or 0,
        "tasks_overdue": tasks_overdue or 0,
        "tasks_completed": tasks_completed or 0,
        "next_due_title": next_due[0] if next_due else None,
        "next_due_date": next_due[1].isoformat() if next_due and next_due[1] else None,
    }
