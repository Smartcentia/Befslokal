from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional
from app.domains.core.models.audit import AuditLog

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        actor: Optional[str] = "system",
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO"
    ):
        log_entry = AuditLog(
            action=action,
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            severity=severity
        )
        db.add(log_entry)
        await db.commit()
        return log_entry

audit_service = AuditService()
