"""
SSB PxWebApi v2 Client – Statistics Norway Statbank.

API docs: https://www.ssb.no/en/api/pxwebapi
No authentication required. Rate limit: 30 requests/min per IP.
"""

from typing import Dict, Any, Optional, List
import httpx
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://data.ssb.no/api/pxwebapi/v2"


class SSBPxWebClient:
    """
    Async client for SSB PxWebApi v2.
    """

    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def search_tables(
        self,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        lang: str = "no",
        include_discontinued: bool = False,
    ) -> Dict[str, Any]:
        """
        Search tables in Statbank Norway.
        GET /tables?query=...&lang=no&pageNumber=1&pageSize=20
        """
        params: Dict[str, Any] = {
            "lang": lang,
            "pageNumber": page,
            "pageSize": page_size,
            "includeDiscontinued": str(include_discontinued).lower(),
        }
        if query:
            params["query"] = query

        url = f"{self.base_url}/tables"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("SSB search_tables HTTP error %s: %s", e.response.status_code, e.response.text)
                raise
            except Exception as e:
                logger.error("SSB search_tables error: %s", e)
                raise

    async def get_table(self, table_id: str, lang: str = "no") -> Dict[str, Any]:
        """
        Get basic info for a table.
        GET /tables/{id}
        """
        url = f"{self.base_url}/tables/{table_id}"
        params = {"lang": lang}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("SSB get_table HTTP error %s: %s", e.response.status_code, e.response.text)
                raise
            except Exception as e:
                logger.error("SSB get_table error: %s", e)
                raise

    async def get_metadata(self, table_id: str, lang: str = "no") -> Dict[str, Any]:
        """
        Get metadata (variables, value codes) for a table.
        GET /tables/{id}/metadata
        """
        url = f"{self.base_url}/tables/{table_id}/metadata"
        params = {"lang": lang}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("SSB get_metadata HTTP error %s: %s", e.response.status_code, e.response.text)
                raise
            except Exception as e:
                logger.error("SSB get_metadata error: %s", e)
                raise

    async def get_data(
        self,
        table_id: str,
        value_codes: Optional[Dict[str, str]] = None,
        selection: Optional[List[Dict[str, Any]]] = None,
        output_format: str = "json-stat2",
        lang: str = "no",
    ) -> Any:
        """
        Get data from a table.

        Either pass value_codes (for GET) or selection (for POST).
        value_codes: {"Tid": "2024*", "Region": "*"} - query params
        selection: [{"variableCode": "Tid", "valueCodes": ["top(3)"]}] - POST body
        """
        url = f"{self.base_url}/tables/{table_id}/data"
        params: Dict[str, Any] = {
            "lang": lang,
            "outputFormat": output_format,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if selection:
                    # POST with selection body
                    body = {"selection": selection}
                    response = await client.post(url, params=params, json=body)
                else:
                    # GET with valueCodes as query params
                    if value_codes:
                        for k, v in value_codes.items():
                            params[f"valueCodes[{k}]"] = v
                    response = await client.get(url, params=params)

                response.raise_for_status()

                if output_format == "json-stat2":
                    return response.json()
                if output_format in ("csv", "html", "xlsx"):
                    return response.content
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("SSB get_data HTTP error %s: %s", e.response.status_code, e.response.text)
                raise
            except Exception as e:
                logger.error("SSB get_data error: %s", e)
                raise
