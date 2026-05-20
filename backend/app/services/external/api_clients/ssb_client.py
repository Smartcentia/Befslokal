from typing import Dict, Any, Optional, List
import httpx
from app.services.external.api_clients.base_client import BaseApiClient, logger

class SSBClient(BaseApiClient):
    """
    Async Client for SSB (Statistics Norway).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url="https://data.ssb.no/api/v0", 
            api_key=api_key, 
            source_name="ssb"
        )

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch.
        """
        return {}

    async def _post(self, endpoint: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform Async POST request.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # No headers needed usually for public SSB stats
                response = await client.post(url, json=json_body)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error posting to {url}: {e}")
                return None

    async def fetch_kpi_data(self, start_year: int, end_year: int) -> Optional[Dict[str, Any]]:
        """
        Fetch KPI data.
        """
        # KPI Table 08184? Or generic.
        endpoint = "/no/table/08184" # Example
        query = {
            "query": [],
            "response": {"format": "json-stat2"}
        }
        
        return await self._post(endpoint, query)
