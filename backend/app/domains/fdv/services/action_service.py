from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.domains.fdv.models.action import WorkOrder, Task
from app.services.base import BaseService
from datetime import datetime
import logging
import uuid

logger = logging.getLogger("ActionService")

class ActionService(BaseService):
    """
    Service for handling actionable items: Work Orders, Tasks, Notifications.
    """
    async def create_work_order(self, db: Session, property_id: str, description: str, priority: str = "medium") -> dict:
        """
        Creates a new work order.
        """
        self.log_info(f"Creating Work Order for Property {property_id}")
        
        try:
            # Validate UUID format (if this was a real app)
            wo = WorkOrder(
                property_id=property_id,
                description=description,
                priority=priority,
                status="pending"
            )
            db.add(wo)
            db.commit()
            db.refresh(wo)
            
            return {
                "order_id": str(wo.order_id),
                "status": "created",
                "message": f"Work order created with priority {priority}"
            }
        except Exception as e:
            db.rollback()
            self.log_error("Failed to create work order", e)
            raise e

    async def create_task(self, db: Session, title: str, action_type: str, payload: dict, order_id: str = None) -> dict:
        """
        Creates a generic task (e.g., 'Send Email', 'Generate Report').
        """
        self.log_info(f"Creating Task: {title} ({action_type})")
        
        try:
            task = Task(
                title=title,
                action_type=action_type,
                payload=payload,
                order_id=order_id,
                status="pending"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # In a real system, we might fire an event here to a background worker
            # to actually execute the task immediately if needed.
            
            return {
                "task_id": str(task.task_id),
                "status": "pending",
                "message": f"Task '{title}' scheduled."
            }
        except Exception as e:
            db.rollback()
            self.log_error("Failed to create task", e)
            raise e

action_service = ActionService()
