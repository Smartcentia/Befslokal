import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.gdpr import DataSubjectRequest, AnonymizationLog
from app.services.base import BaseService
import logging

logger = logging.getLogger("GDPRService")

class GDPRService(BaseService):
    """
    Service for GDPR compliance: PII detection and anonymization.
    """
    def __init__(self):
        # Baseline patterns. In production, use a dedicated PII detection service.
        self.pii_patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "ssn": r"\d{6}\s?\d{5}", # Simple Norwegian SSN-like pattern
            "phone": r"\+?\d{8,}"
        }

    async def detect_pii(self, text: str) -> List[dict]:
        """
        Scans text for PII.
        """
        matches = []
        for pii_type, pattern in self.pii_patterns.items():
            for match in re.finditer(pattern, text):
                matches.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        return matches

    async def anonymize_text(self, db: Session, text: str, entity_type: str = "unknown", entity_id: str = "unknown") -> str:
        """
        Replaces PII with [MASKED].
        """
        anonymized_text = text
        matches = await self.detect_pii(text)
        
        # Sort matches by start position in reverse to avoid index shifting
        matches.sort(key=lambda x: x["start"], reverse=True)
        
        for match in matches:
            start, end = match["start"], match["end"]
            anonymized_text = anonymized_text[:start] + f"[{match['type'].upper()}_REDACTED]" + anonymized_text[end:]
            
            # Log the action
            log = AnonymizationLog(
                entity_type=entity_type,
                entity_id=entity_id,
                original_pii_type=match["type"],
                action="masked"
            )
            db.add(log)
            
        if matches:
            await db.commit()
            
        return anonymized_text

    async def create_request(self, db: Session, user_id: str, request_type: str, details: dict) -> dict:
        """
        Logs a formalized GDPR request.
        """
        req = DataSubjectRequest(
            user_id=user_id,
            request_type=request_type,
            details=details,
            status="pending"
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return {"request_id": str(req.request_id), "status": "pending"}

gdpr_service = GDPRService()
