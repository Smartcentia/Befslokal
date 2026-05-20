"""
Follow-up service for overdue internal control cases.
Processes overdue cases, sends reminders, and escalates when needed.
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.domains.hms.models.internal_control import InternalControlCase, Notification
import logging

logger = logging.getLogger(__name__)

REMINDER_1_DAYS = 1
REMINDER_2_DAYS = 3
ESCALATION_DAYS = 7


class FollowUpService:
    @staticmethod
    async def process_overdue_cases(db: AsyncSession) -> Dict[str, Any]:
        """
        Process all overdue internal control cases.
        - First reminder: 1 day overdue
        - Second reminder: 3 days overdue
        - Escalation: 7 days overdue
        """
        now = datetime.utcnow()
        stats = {
            "total_overdue": 0,
            "reminded_1": 0,
            "reminded_2": 0,
            "escalated": 0,
            "notifications_sent": 0,
            "errors": 0,
        }

        result = await db.execute(
            select(InternalControlCase).where(
                and_(
                    InternalControlCase.status == "open",
                    InternalControlCase.due_date.isnot(None),
                    InternalControlCase.due_date < now,
                )
            )
        )
        overdue_cases = result.scalars().all()
        stats["total_overdue"] = len(overdue_cases)

        for case in overdue_cases:
            try:
                due = case.due_date
                if due is None:
                    continue
                due_naive = due.replace(tzinfo=None) if due.tzinfo else due
                days_overdue = max(0, (now - due_naive).days)
                due_str = due_naive.strftime("%d.%m.%Y")
                follow_status = case.follow_up_status or "none"

                if days_overdue >= ESCALATION_DAYS and follow_status != "escalated":
                    case.follow_up_status = "escalated"
                    case.escalated_at = now
                    stats["escalated"] += 1
                    if case.assigned_user_id:
                        notif = Notification(
                            user_id=str(case.assigned_user_id),
                            title=f"Eskalert: {case.title}",
                            message=f"Saken er {days_overdue} dager forfalt og er eskalert. Frist var {due_str}.",
                            notification_type="internal_control",
                            related_entity_type="case",
                            related_entity_id=str(case.case_id),
                        )
                        db.add(notif)
                        stats["notifications_sent"] += 1
                    logger.info(f"Escalated case {case.case_id} ({days_overdue} days overdue)")

                elif days_overdue >= REMINDER_2_DAYS and follow_status not in ("reminded_2", "escalated"):
                    case.follow_up_status = "reminded_2"
                    case.last_reminder_at = now
                    stats["reminded_2"] += 1
                    if case.assigned_user_id:
                        notif = Notification(
                            user_id=str(case.assigned_user_id),
                            title=f"Purring 2: {case.title}",
                            message=f"Saken er {days_overdue} dager forfalt. Frist var {due_str}.",
                            notification_type="internal_control",
                            related_entity_type="case",
                            related_entity_id=str(case.case_id),
                        )
                        db.add(notif)
                        stats["notifications_sent"] += 1

                elif days_overdue >= REMINDER_1_DAYS and follow_status == "none":
                    case.follow_up_status = "reminded_1"
                    case.last_reminder_at = now
                    stats["reminded_1"] += 1
                    if case.assigned_user_id:
                        notif = Notification(
                            user_id=str(case.assigned_user_id),
                            title=f"Purring: {case.title}",
                            message=f"Saken er forfalt. Frist var {due_str}.",
                            notification_type="internal_control",
                            related_entity_type="case",
                            related_entity_id=str(case.case_id),
                        )
                        db.add(notif)
                        stats["notifications_sent"] += 1

            except Exception as e:
                logger.error(f"Error processing case {case.case_id}: {e}")
                stats["errors"] += 1

        await db.commit()
        logger.info(f"Follow-up processing complete: {stats}")
        return stats
