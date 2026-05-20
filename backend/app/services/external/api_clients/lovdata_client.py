from typing import Dict, Any, Optional, List
import logging
from app.services.external.api_clients.base_client import BaseApiClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class LovdataClient(BaseApiClient):
    """
    Client for Lovdata API.
    Based on documentation: https://api.lovdata.no
    """
    
    def __init__(self, api_key: Optional[str] = None):
        base_url = getattr(settings, "LOVDATA_BASE_URL", "https://api.lovdata.no")
        super().__init__(
            base_url=base_url,
            api_key=api_key or getattr(settings, "LOVDATA_API_KEY", None),
            source_name="lovdata",
            api_key_header_name="X-API-KEY"  # Example, verify exact header in docs
        )

    async def search(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        Full-text search for laws and regulations.
        """
        params = {
            "q": query,
            "limit": limit,
            "offset": offset
        }
        return await self._get("search", params=params)

    async def get_public_data_list(self) -> Dict[str, Any]:
        """
        List available open datasets.
        """
        return await self._get("public/datasets")

    async def get_public_data(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific open dataset.
        """
        return await self._get(f"public/datasets/{dataset_id}")

    async def get_document_meta(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve metadata for a specific document.
        """
        return await self._get(f"document/{document_id}/meta")

    async def lookup(self, reference: str) -> Dict[str, Any]:
        """
        Check if a document or reference exists.
        """
        params = {"ref": reference}
        return await self._get("lookup", params=params)

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch implementation for BaseApiClient.
        """
        return await self.get_document_meta(identifier)
