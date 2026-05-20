from typing import Dict, Any, Optional, List
from .base_client import BaseApiClient
from app.core.config import settings

class PlanslurpenClient(BaseApiClient):
    """
    Client for Planslurpen API (Zoning and Planning data).
    Documentation: https://www.planslurpen.no/api/swagger/index.html
    """
    
    def __init__(self):
        # Default base URL if not in settings
        base_url = os.getenv("PLANSLURPEN_BASE_URL", "https://www.planslurpen.no/api")
        super().__init__(
            base_url=base_url,
            api_key=settings.PLANSLURPEN_API_KEY,
            source_name="planslurpen"
        )

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch_data implementation required by BaseApiClient.
        Resolves to fetch_plans_by_matrikkel if matrikkel-like identifier.
        """
        if identifier.count('-') == 2: # Simple check for knr-gnr-bnr format
            knr, gnr, bnr = identifier.split('-')
            return await self.fetch_plans_by_matrikkel(knr, gnr, bnr)
        return await self.get_plan_details(identifier)

    async def fetch_plans_by_matrikkel(self, knr: str, gnr: str, bnr: str) -> Dict[str, Any]:
        """
        Fetch plans associated with a specific property (matrikkel).
        """
        endpoint = f"Planregister/Matrikkel/{knr}/{gnr}/{bnr}"
        try:
            return await self._get(endpoint)
        except Exception:
            # According to docs, some endpoints might be structured differently
            # Fallback or alternative structure if needed
            return {"plans": [], "message": "No plans found or API structure mismatch"}

    async def get_plan_details(self, plan_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific plan.
        """
        endpoint = f"Plan/{plan_id}"
        return await self._get(endpoint)

    async def get_plan_regulations(self, plan_id: str) -> Dict[str, Any]:
        """
        Get regulations (bestemmelser) for a specific plan.
        """
        endpoint = f"Plan/{plan_id}/Bestemmelser"
        return await self._get(endpoint)

import os # Required for getenv in __init__
