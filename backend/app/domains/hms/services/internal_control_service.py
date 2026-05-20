from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, func, select
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.domains.core.models.user import User
from app.domains.fdv.models.action import Task, WorkOrder
from app.schemas.internal_control import InternalControlCaseCreate
from app.domains.hms.models.internal_control import InternalControlCase, Notification
from app.domains.core.models.property import Property
import logging

logger = logging.getLogger(__name__)

class InternalControlService:
    
    @staticmethod
    async def get_case(db: AsyncSession, case_id: uuid.UUID):
        query = select(InternalControlCase).filter(
            (InternalControlCase.case_id == str(case_id)) | 
            (InternalControlCase.risk_assessment_id == str(case_id))
        ).options(
            selectinload(InternalControlCase.property).selectinload(Property.managers),
            selectinload(InternalControlCase.assigned_user)
        )
        
        result = await db.execute(query)
        case = result.scalars().first()
        return case

    @staticmethod
    async def get_property_cases(
        db: AsyncSession,
        property_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ):
        from sqlalchemy import func

        query = select(InternalControlCase)
        if property_id:
            query = query.filter(InternalControlCase.property_id == str(property_id))
        if status:
            query = query.filter(func.lower(InternalControlCase.status) == status.lower())
        if priority:
            query = query.filter(func.lower(InternalControlCase.priority) == priority.lower())
        
        # Ensure property.managers is also loaded via selectinload to avoid MissingGreenlet errors in serialization
        query = query.options(
            selectinload(InternalControlCase.property).selectinload(Property.managers),
            selectinload(InternalControlCase.assigned_user)
        ).order_by(InternalControlCase.due_date.asc())
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_activity_wheel_summary(db: AsyncSession, property_ids: Optional[List[uuid.UUID]] = None):
        from app.schemas.internal_control import ActivityWheelItem, ActivityWheelSummary
        from datetime import datetime, timezone

        query = select(InternalControlCase)
        if property_ids is not None:
            if not property_ids:
                return ActivityWheelSummary(items=[], total_cases=0)
            # Match types - use strings if needed
            query = query.filter(InternalControlCase.property_id.in_(property_ids))
        
        result = await db.execute(query)
        cases = result.scalars().all()
        
        # Localize now to UTC if comparing with UTC dates
        now = datetime.now(timezone.utc)
        
        summary = {}
        for case in cases:
            ctype = case.case_type or "Annet"
            # Norwegian translation for common types
            display_name = {
                "monthly": "Månedlig",
                "quarterly": "Kvartalsvis",
                "annual": "Årlig",
                "weekly": "Ukentlig",
                "daily": "Daglig"
            }.get(ctype.lower(), ctype.capitalize())

            if display_name not in summary:
                summary[display_name] = {"total": 0, "completed": 0, "open": 0, "overdue": 0}
            
            summary[display_name]["total"] += 1
            if case.status in ["closed", "completed"]:
                summary[display_name]["completed"] += 1
            else:
                summary[display_name]["open"] += 1
                if case.due_date:
                    # Handle timezone aware/naive mismatch
                    due = case.due_date
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=timezone.utc)
                        
                    if due < now:
                        summary[display_name]["overdue"] += 1
        
        items = [
            ActivityWheelItem(
                name=k,
                total=v["total"],
                completed=v["completed"],
                open=v["open"],
                overdue=v["overdue"]
            ) for k, v in summary.items()
        ]
        
        # Sort by typical order
        order = ["Daglig", "Ukentlig", "Månedlig", "Kvartalsvis", "Årlig"]
        items.sort(key=lambda x: order.index(x.name) if x.name in order else 99)
        
        return ActivityWheelSummary(items=items, total_cases=len(cases))

    @staticmethod
    async def create_initial_cases_for_property(db: AsyncSession, property_id: uuid.UUID, assigned_user_id: Optional[uuid.UUID] = None):
        result = await db.execute(select(Property).filter(Property.property_id == str(property_id)))
        prop = result.scalars().first()
        if not prop:
            return []

        # Load templates via helper
        import json
        import os
        from typing import List, Dict, Any

        TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "internal_control_templates.json")

        try:
            with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
                templates = json.load(f)
        except FileNotFoundError:
            # Fallback for dev if file missing
            logger.warning("Templates not found at %s, using empty list.", TEMPLATE_PATH)
            templates = []

        # Determine applicable templates based on property usage
        # In this context, we check if property is an institution (RKL6 relevant)
        property_usage = (prop.usage or "").upper()
        
        applicable_templates = []
        for t in templates:
            template_usage = t.get("building_type", "ANY")
            if template_usage == "ANY" or template_usage in property_usage:
                applicable_templates.append(t)
            elif "INSTITUSJON" in property_usage and template_usage == "INSTITUTION":
                applicable_templates.append(t)

        if not applicable_templates and not templates:
             # Keep old fallback if JSON empty
             applicable_templates = [
                {
                    "title": f"Månedlig brannvern sjekk - {prop.address}", 
                    "description": "Sjekk av brannslukningsapparater.", 
                    "type": "monthly_check", 
                    "days_frequency": 30
                }
             ]

        created_cases = []
        for t in applicable_templates:
            # Format checklist into description or process_data
            checklist_text = "\n".join([f"- [{item.get('responsibility', 'UNKNOWN')}] {item['task']} ({item.get('criticality', 'LOW')})" for item in t.get("checklist_items", [])])
            
            # Store structured checklist in process_data for frontend rendering
            process_data = {
                "checklist": t.get("checklist_items", []),
                "template_id": t.get("template_id"),
                "risk_class": 6,
                "legal_references": t.get("legal_references", [])
            }

            case = InternalControlCase(
                property_id=str(property_id),
                assigned_user_id=str(assigned_user_id) if assigned_user_id else None,
                title=f"{t['title']} - {prop.address}",
                description=t.get("description", "") + "\n\nSjekkpunkter:\n" + checklist_text,
                case_type=t.get("type", "other"),
                priority="high" if "rkl6" in t.get("template_id", "") else "medium",
                due_date=datetime.utcnow() + timedelta(days=t.get("days_frequency", 30)),
                status="open",
                process_data=process_data, # Store structured data
                process_state="Opprettet"
            )
            db.add(case)
            created_cases.append(case)
            
        await db.flush() # get IDs
        
        # Create notifications
        if assigned_user_id:
            for case in created_cases:
                await InternalControlService.create_notification(
                    db=db,
                    user_id=assigned_user_id,
                    title=f"Ny IK-oppgave: {case.title}",
                    message=f"Du har fått tildelt en ny oppgave for {prop.address}. Frist: {case.due_date.strftime('%d.%m.%Y')}",
                    related_entity_id=case.case_id
                )

        await db.commit()
        return created_cases

    @staticmethod
    async def create_case_from_template(
        db: AsyncSession,
        template_id: uuid.UUID,
        property_id: uuid.UUID,
        assigned_user_id: Optional[uuid.UUID] = None,
    ) -> Optional[InternalControlCase]:
        """
        Opprett InternalControlCase fra en ChecklistTemplate.
        Konverterer template items til process_data.checklist-format.
        """
        from app.domains.hms.models.checklist import ChecklistTemplate

        result = await db.execute(
            select(ChecklistTemplate).where(ChecklistTemplate.template_id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            return None

        result = await db.execute(select(Property).filter(Property.property_id == str(property_id)))
        prop = result.scalar_one_or_none()
        if not prop:
            return None

        # Konverter ChecklistTemplate items til process_data.checklist-format
        # Template items: [{"id": "1", "label": "..."}] eller [{"task": "...", "responsibility": "...", "criticality": "..."}]
        checklist_items = []
        for i, item in enumerate(template.items or []):
            if isinstance(item, dict):
                task = item.get("task") or item.get("label", str(item))
                checklist_items.append({
                    "task": task,
                    "responsibility": item.get("responsibility", "TENANT"),
                    "criticality": item.get("criticality", "MEDIUM"),
                })
            else:
                checklist_items.append({
                    "task": str(item),
                    "responsibility": "TENANT",
                    "criticality": "MEDIUM",
                })

        process_data = {
            "checklist": checklist_items,
            "template_id": str(template_id),
            "source": "checklist_template",
        }

        case = InternalControlCase(
            property_id=str(property_id),
            assigned_user_id=str(assigned_user_id) if assigned_user_id else None,
            title=f"{template.title} - {prop.address or prop.name or 'Eiendom'}",
            description=template.description or "",
            case_type="user_checklist",
            priority="medium",
            due_date=datetime.utcnow() + timedelta(days=30),
            status="open",
            process_data=process_data,
            process_state="Opprettet",
        )
        db.add(case)
        await db.flush()

        if assigned_user_id:
            await InternalControlService.create_notification(
                db=db,
                user_id=assigned_user_id,
                title=f"Ny sjekkliste: {case.title}",
                message=f"Du har fått en ny sjekkliste basert på malen «{template.title}».",
                related_entity_id=case.case_id,
            )

        await db.commit()
        await db.refresh(case)
        return case

    @staticmethod
    async def complete_checklist(
        db: AsyncSession,
        case_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        responses: dict,
        notes: Optional[str] = None
    ) -> Optional[InternalControlCase]:
        """
        Complete a checklist on an internal control case.
        Updates process_data with responses, sets status=closed, completed_at=now.
        """
        case = await InternalControlService.get_case(db, case_id)
        if not case:
            return None

        now = datetime.utcnow()
        current_data = dict(case.process_data) if case.process_data else {}
        current_data["checklist_responses"] = responses
        current_data["completed_by"] = str(user_id) if user_id else None
        current_data["completed_at"] = now.isoformat()
        if notes:
            current_data["completion_notes"] = notes

        case.process_data = current_data
        case.status = "closed"
        case.completed_at = now
        case.notes = (case.notes or "") + (f"\nFullført: {notes}" if notes else "")

        await db.commit()
        await db.refresh(case)
        return case

    @staticmethod
    async def get_user_notifications(db: AsyncSession, user_id: uuid.UUID, unread_only: bool = False):
        query = select(Notification).filter(Notification.user_id == str(user_id))
        if unread_only:
            query = query.filter(Notification.is_read == False)
        query = query.order_by(desc(Notification.created_at))
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_notification(db: AsyncSession, user_id: uuid.UUID, title: str, message: str, related_entity_id: Optional[uuid.UUID] = None):
        notification = Notification(
            user_id=str(user_id),
            title=title,
            message=message,
            notification_type="internal_control",
            related_entity_type="case",
            related_entity_id=str(related_entity_id) if related_entity_id else None,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        # Note: commit is usually called by caller, but for helper methods we might want to avoid partial commits. 
        # But InternalControlService manages transaction. 
        # If called independently, caller must commit.
        return notification

    @staticmethod
    async def mark_notification_as_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID):
        result = await db.execute(select(Notification).filter(
            Notification.notification_id == str(notification_id),
            Notification.user_id == str(user_id)
        ))
        notif = result.scalars().first()
        if notif:
            notif.is_read = True
            notif.read_at = datetime.utcnow()
            await db.commit()
        return notif

    @staticmethod
    async def generate_daily_tasks(db: AsyncSession):
        """
        Main engine to generate daily checklists based on property tags.
        """
        logger.info("Starting daily task generation for IK-Bygg...")
        
        # 1. Fetch all properties with their tags
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        tasks_created = 0
        
        for prop in properties:
            if not prop.external_data:
                continue
                
            tags = prop.external_data.get("tags", {})
            p_type = tags.get("type") # Institusjon / Kontor
            risk_class = tags.get("risk_class") # RKL6
            
            # --- LOGIC RULE 1: Institution Daily Checks ---
            if p_type == "Institusjon":
                # Brannsentral Check
                await InternalControlService._create_task(
                    db,
                    prop.property_id, 
                    title="Sjekk brannsentral (Grønt lys?)", 
                    priority="High"
                )
                tasks_created += 1
                
                # Escape Route Check
                await InternalControlService._create_task(
                    db,
                    prop.property_id, 
                    title="Sjekk at rømningveier er fri for rot/lager", 
                    priority="Critical"
                )
                tasks_created += 1

            # --- LOGIC RULE 2: Risk Class 6 (RKL6) Specifics ---
            if risk_class == "RKL6":
                # Check locks
                await InternalControlService._create_task(
                    db,
                    prop.property_id,
                    title="Test av nødåpner på dører (Sikkerhet vs Rømning)",
                    priority="Critical"
                )
                tasks_created += 1
                
            # --- LOGIC RULE 3: Office (Kontor) Checks ---
            if p_type == "Kontor":
                await InternalControlService._create_task(
                    db,
                    prop.property_id,
                    title="HMS Runde: Sjekk ergonomi og belysning",
                    priority="Medium"
                )
                tasks_created += 1
                
        await db.commit()
        logger.info(f"Daily task generation complete. Created {tasks_created} tasks.")
        return tasks_created

    @staticmethod
    async def _create_task(db: AsyncSession, property_id, title, priority):
        task = Task(
            title=title,
            status="pending",
            payload={"priority": priority, "auto_generated": True, "source": "IK-Bygg Engine"}
        )
        # Note: Task model currently links to WorkOrder, not directly Property.
        # We might need to create a wrapper WorkOrder or link Task to Property in Schema v2.
        # For now, let's assume we link to a "Daily Checklist" WorkOrder.
        
        # Create a Work Order bucket for today if not exists (Simplified)
        wo = WorkOrder(
            property_id=property_id,
            description=f"Daglig Sjekkliste {datetime.now().strftime('%Y-%m-%d')}",
            status="pending",
            priority=priority
        )
        db.add(wo)
        await db.flush() # Get ID
        
        task.order_id = wo.order_id
        db.add(task)
        return task

    @staticmethod
    async def handle_deviation(db: AsyncSession, deviation_data: dict, user: User):
        """
        Workflow Engine for deviations.
        """
        prop_id = deviation_data.get("property_id")
        stmt = select(Property).where(Property.property_id == prop_id)
        result = await db.execute(stmt)
        prop = result.scalar_one_or_none()
        
        if not prop:
            raise ValueError("Property not found")
            
        tags = prop.external_data.get("tags", {})
        ownership = tags.get("ownership") # Eid / Leid
        
        # --- LOGIC RULE 4: Tenant Workflow ---
        if ownership == "Leid":
            # Deviation on Leased property -> Notify Landlord
            logger.info(f"Deviation on Leased property {prop.name}. Triggering External Workflow.")
            return {
                "action": "notify_landlord",
                "message": f"Avvik sendt til gårdeier for {prop.name}. Status: Venter på ekstern utbedring."
            }
        else:
            # Owned property -> Internal Work Order
            logger.info(f"Deviation on Owned property {prop.name}. Creating Internal WO.")
            return {
                "action": "create_internal_wo",
                "message": "Arbeidsordre opprettet for intern drift."
            }
