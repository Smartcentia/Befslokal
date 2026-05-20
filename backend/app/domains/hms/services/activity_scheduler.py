"""
Activity Scheduler Service
Runs as background task to create InternalControlCase from ScheduledActivity
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.domains.hms.models.scheduled_activity import ScheduledActivity
from app.domains.hms.models.internal_control import InternalControlCase, Notification
from app.domains.hms.services.activity_generator import ActivityGenerator

logger = logging.getLogger(__name__)


class ActivityScheduler:
    """
    Background scheduler that checks for due activities and generates InternalControlCases.
    Should be run daily via cron or APScheduler.
    """
    
    async def process_due_activities(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Process all activities that are due today or overdue.
        Creates InternalControlCase for each due activity and advances the next_due_date.
        """
        now = datetime.now()
        
        # Find all enabled activities that are due
        result = await db.execute(
            select(ScheduledActivity).where(
                and_(
                    ScheduledActivity.enabled == True,
                    ScheduledActivity.next_due_date <= now
                )
            )
        )
        due_activities = result.scalars().all()
        
        stats = {
            "total_due": len(due_activities),
            "cases_created": 0,
            "notifications_sent": 0,
            "errors": 0
        }
        
        for activity in due_activities:
            try:
                # Create InternalControlCase
                case = InternalControlCase(
                    property_id=activity.property_id,
                    title=activity.title,
                    description=activity.description,
                    case_type=activity.activity_type,
                    status="open",
                    priority=activity.priority,
                    due_date=activity.next_due_date,
                    assigned_user_id=activity.assigned_user_id,
                    notes=f"Automatisk generert fra planlagt aktivitet: {activity.activity_id}"
                )
                db.add(case)
                stats["cases_created"] += 1
                
                # Create notification if user is assigned
                if activity.assigned_user_id:
                    notification = Notification(
                        user_id=activity.assigned_user_id,
                        title=f"Ny HMS-oppgave: {activity.title}",
                        message=f"{activity.description}\nForfallsdato: {activity.next_due_date.strftime('%d.%m.%Y')}",
                        notification_type="internal_control",
                        related_entity_type="case",
                        related_entity_id=case.case_id
                    )
                    db.add(notification)
                    stats["notifications_sent"] += 1
                
                # Calculate next due date
                next_due = ActivityGenerator.calculate_next_due_date(
                    activity.recurrence_rule,
                    from_date=activity.next_due_date
                )
                activity.next_due_date = next_due
                activity.last_generated_at = now
                
                logger.info(
                    f"Processed activity {activity.activity_id}: "
                    f"Created case, next due: {next_due}"
                )
                
            except Exception as e:
                logger.error(f"Error processing activity {activity.activity_id}: {e}")
                stats["errors"] += 1
                continue
        
        await db.commit()
        
        logger.info(f"Activity processing complete: {stats}")
        return stats
    
    async def get_upcoming_activities(
        self, 
        db: AsyncSession, 
        days_ahead: int = 7,
        property_id: str = None,
        user_id: str = None
    ):
        """
        Get activities due within the next N days for calendar display.
        """
        now = datetime.now()
        future_date = now + timedelta(days=days_ahead)
        
        query = select(ScheduledActivity).where(
            and_(
                ScheduledActivity.enabled == True,
                ScheduledActivity.next_due_date >= now,
                ScheduledActivity.next_due_date <= future_date
            )
        )
        
        if property_id:
            query = query.where(ScheduledActivity.property_id == property_id)
        
        if user_id:
            query = query.where(ScheduledActivity.assigned_user_id == user_id)
        
        result = await db.execute(query.order_by(ScheduledActivity.next_due_date))
        return result.scalars().all()

    async def trigger_specific_activity(self, db: AsyncSession, activity_id: Any) -> InternalControlCase:
        """
        Manually trigger a specific activity to create a case immediately.
        Advances the next_due_date.
        """
        result = await db.execute(
            select(ScheduledActivity).where(ScheduledActivity.activity_id == activity_id)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            return None
            
        now = datetime.now()
        
        # Create InternalControlCase
        case = InternalControlCase(
            property_id=activity.property_id,
            title=activity.title,
            description=activity.description,
            case_type=activity.activity_type,
            status="open",
            priority=activity.priority,
            due_date=activity.next_due_date,
            assigned_user_id=activity.assigned_user_id,
            notes=f"Manuelt startet fra planlagt aktivitet i kalender: {activity.activity_id}"
        )
        db.add(case)
        
        # Calculate next due date
        next_due = ActivityGenerator.calculate_next_due_date(
            activity.recurrence_rule,
            from_date=activity.next_due_date
        )
        activity.next_due_date = next_due
        activity.last_generated_at = now
        
        await db.commit()
        await db.refresh(case)
        
        return case
