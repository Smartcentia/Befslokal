
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from app.domains.core.models.property import Property
from app.domains.fdv.models.action import Task, WorkOrder
from app.domains.core.models.user import User

logger = logging.getLogger(__name__)

class InternalControlService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_daily_tasks(self):
        """
        Main engine to generate daily checklists based on property tags.
        """
        logger.info("Starting daily task generation for IK-Bygg...")
        
        # 1. Fetch all properties with their tags
        stmt = select(Property)
        result = await self.db.execute(stmt)
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
                await self._create_task(
                    prop.property_id, 
                    title="Sjekk brannsentral (Grønt lys?)", 
                    priority="High"
                )
                
                # Escape Route Check
                await self._create_task(
                    prop.property_id, 
                    title="Sjekk at rømningveier er fri for rot/lager", 
                    priority="Critical"
                )

            # --- LOGIC RULE 2: Risk Class 6 (RKL6) Specifics ---
            if risk_class == "RKL6":
                # Check locks
                await self._create_task(
                    prop.property_id,
                    title="Test av nødåpner på dører (Sikkerhet vs Rømning)",
                    priority="Critical"
                )
                
            # --- LOGIC RULE 3: Office (Kontor) Checks ---
            if p_type == "Kontor":
                await self._create_task(
                    prop.property_id,
                    title="HMS Runde: Sjekk ergonomi og belysning",
                    priority="Medium"
                )
                
        await self.db.commit()
        logger.info(f"Daily task generation complete. Created {tasks_created} tasks.")
        return tasks_created

    async def _create_task(self, property_id, title, priority):
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
        self.db.add(wo)
        await self.db.flush() # Get ID
        
        task.order_id = wo.order_id
        self.db.add(task)
        return task

    async def handle_deviation(self, deviation_data: dict, user: User):
        """
        Workflow Engine for deviations.
        """
        prop_id = deviation_data.get("property_id")
        stmt = select(Property).where(Property.property_id == prop_id)
        prop = (await self.db.execute(stmt)).scalar_one_or_none()
        
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
