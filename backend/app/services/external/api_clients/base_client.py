from typing import Dict, Any, Optional
import httpx
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseApiClient(ABC):
    """
    Base async API client using httpx.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        source_name: str = "external_api",
        api_key_header_name: str = "Authorization"
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.source_name = source_name
        self.timeout = timeout
        self.api_key_header_name = api_key_header_name

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform Async GET request.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Construct headers with API key if present.
        """
        headers = {}
        if self.api_key:
            if self.api_key_header_name == "Authorization":
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers[self.api_key_header_name] = self.api_key
        return headers

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform Async GET request.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error {e.response.status_code} for {url}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise

    @abstractmethod
    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        pass
