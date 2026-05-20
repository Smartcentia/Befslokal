from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from app.domains.innsikt.models.memory import UserPreference, ContextHistory
from app.services.base import BaseService
import logging

logger = logging.getLogger("MemoryService")

class MemoryService(BaseService):
    """
    Service for managing User Memory and Context.
    """
    async def get_user_preferences(self, db: Session, user_id: str) -> dict:
        """
        Retrieves user preferences, creating default if not exists.
        """
        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not pref:
            self.log_info(f"Creating default preferences for user {user_id}")
            pref = UserPreference(user_id=user_id)
            db.add(pref)
            db.commit()
            db.refresh(pref)
        
        return {
            "user_id": pref.user_id,
            "language": pref.language,
            "notifications": pref.notifications,
            "ui_settings": pref.ui_settings
        }

    async def update_user_preferences(self, db: Session, user_id: str, updates: dict) -> dict:
        """
        Updates specific preference fields.
        """
        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not pref:
            pref = UserPreference(user_id=user_id)
            db.add(pref)
        
        if "language" in updates:
            pref.language = updates["language"]
        if "notifications" in updates:
            # Merge logic could be more complex
            pref.notifications = {**pref.notifications, **updates["notifications"]}
        if "ui_settings" in updates:
            pref.ui_settings = {**pref.ui_settings, **updates["ui_settings"]}
            
        db.commit()
        db.refresh(pref)
        return await self.get_user_preferences(db, user_id)

    async def log_context(self, db: Session, user_id: str, content: dict, interaction_type: str = "chat"):
        """
        Logs an interaction to history.
        """
        try:
            ctx = ContextHistory(
                user_id=user_id,
                interaction_type=interaction_type,
                content=content
            )
            db.add(ctx)
            db.commit()
        except Exception as e:
            self.log_error("Failed to log context", e)
            # Non-blocking error

memory_service = MemoryService()
