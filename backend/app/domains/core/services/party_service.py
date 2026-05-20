from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domains.core.models.party import Party
from app.services.external.brreg_service import BrregService
from app.services.search.indexer import index_api_data
from app.services.infrastructure.logger import get_logger
import logging

logger = get_logger(__name__)

class PartyService:
    """
    Service for managing Party entities, including fetching from BRRG
    and persisting to local DB + Vector DB.
    """

    @staticmethod
    async def fetch_and_store_party(org_nr: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Fetches party data from BRREG, persists/updates it in PostgreSQL,
        and indexes it in ChromaDB.
        
        Returns the raw data dictionary (similar to what BrregService returns)
        or None if not found/error.
        """
        # 1. Fetch from BRREG
        brreg_data = await BrregService.get_enhet(org_nr, db=db)
        
        if not brreg_data:
            logger.warning(f"PartyService: Could not fetch data for OrgNr {org_nr}")
            return None

        # 2. Extract key fields
        name = brreg_data.get("name")
        address = brreg_data.get("address")
        
        # 3. Upsert in PostgreSQL
        try:
            # Check if exists
            query = select(Party).filter(Party.orgnr == org_nr)
            result = await db.execute(query)
            existing_party = result.scalar_one_or_none()

            if existing_party:
                # Update existing
                logger.debug("PartyService: Updating existing party %s", org_nr)
                existing_party.name = name
                # Merge new external data with existing if any
                if existing_party.external_data:
                    # Make a copy to ensure mutation is tracked if it's a MutableDict property, 
                    # but typically replacing the dict is safer for SQLA detection.
                    updated_data = dict(existing_party.external_data)
                    updated_data.update(brreg_data)
                    existing_party.external_data = updated_data
                else:
                     existing_party.external_data = brreg_data
            else:
                # Create new
                logger.debug("PartyService: Creating new party %s", org_nr)
                new_party = Party(
                    name=name,
                    orgnr=org_nr,
                    external_data=brreg_data,
                    # Optional: Parse address to separate fields if Party model supports it
                )
                db.add(new_party)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"PartyService: Database error persisting party {org_nr}: {e}")
            await db.rollback()
            # We continue even if DB fails, to return the data at least? 
            # Or should we fail? Given this is "fetch_and_store", maybe we log and return data.
        
        # 4. Index in Vector DB (ChromaDB)
        try:
            # Add metadata for indexing
            indexing_data = dict(brreg_data)
            indexing_data["entity_type"] = "party"
            indexing_data["source"] = "brreg_import"
            
            # Note: index_api_data is sync, might block slightly. 
            # Ideally run in executor if heavy.
            index_result = index_api_data(indexing_data)
            logger.debug("PartyService: Indexed party %s in Vector DB. Result: %s", org_nr, index_result)
            
        except Exception as e:
            logger.error(f"PartyService: Vector indexing error for party {org_nr}: {e}")
            # Non-blocking failure for indexing
        
        return brreg_data
