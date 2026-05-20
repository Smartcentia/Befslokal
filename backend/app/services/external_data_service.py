import logging
from typing import Any, Optional, Dict
from sqlalchemy.orm import Session
from app.models.external_api_data import ExternalApiData
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class ExternalDataService:
    @staticmethod
    async def save_api_data(
        db: AsyncSession,
        source: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        ttl_hours: int = 24
    ):
        """
        Saves or updates external API data in the database.
        """
        try:
            # Check if exists
            stmt = select(ExternalApiData).filter(
                ExternalApiData.source_api == source,
                ExternalApiData.entity_type == entity_type,
                ExternalApiData.entity_id == entity_id
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            expires_at = datetime.now() + timedelta(hours=ttl_hours)

            if existing:
                existing.data = data
                existing.fetched_at = datetime.now()
                existing.expires_at = expires_at
            else:
                new_entry = ExternalApiData(
                    source_api=source,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    data=data,
                    expires_at=expires_at
                )
                db.add(new_entry)
            
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to save external API data: {e}")
            # Vi ruller ikke ut her, lar kalleren håndtere transaksjonen
            raise e

    @staticmethod
    async def get_cached_api_data(
        db: AsyncSession,
        source: str,
        entity_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached API data.
        """
        try:
            stmt = select(ExternalApiData).filter(
                ExternalApiData.source_api == source,
                ExternalApiData.entity_type == entity_type,
                ExternalApiData.entity_id == entity_id
            )
            result = await db.execute(stmt)
            entry = result.scalar_one_or_none()

            if entry:
                return entry.data
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve external API data: {e}")
            return None
