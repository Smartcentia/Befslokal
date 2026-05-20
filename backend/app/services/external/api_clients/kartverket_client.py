from typing import Dict, Any, Optional
import re
from app.services.external.api_clients.base_client import BaseApiClient, logger


class KartverketClient(BaseApiClient):
    """
    Async Client for Kartverket APIs (Matrikkel, KommuneInfo).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Using Geonorge equivalent or similar public APIs if possible, 
        # but adhering to external repo structure.
        super().__init__(
            base_url="https://api.kartverket.no", # Placeholder, adjust as needed
            api_key=api_key,
            source_name="kartverket"
        )
        self.ws_kommune_url = "https://ws.geonorge.no/kommuneinfo/v1"
        self.ws_stedsnavn_url = "https://ws.geonorge.no/stedsnavn/v1"

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
         parts = identifier.split(",")
         if len(parts) == 2:
             return await self.get_kommune_from_point(float(parts[0]), float(parts[1]))
         return {}

    async def get_kommune_from_point(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get Kommune info (code, name) from coordinates.
        Useful for NVE Flood Forecast mapping.
        """
        # Endpoint: https://ws.geonorge.no/kommuneinfo/v1/punkt?nord=...&ost=...&koordsys=4326
        url = f"{self.ws_kommune_url}/punkt"
        params = {
            "nord": latitude,
            "ost": longitude,
            "koordsys": 4326
        }
        
        import httpx
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                kommunenummer = data.get("kommunenummer")
                fylkesnummer = data.get("fylkesnummer")
                
                if not fylkesnummer and kommunenummer and len(kommunenummer) >= 2:
                    fylkesnummer = kommunenummer[:2]

                return {
                    "kommunenummer": kommunenummer,
                    "kommunenavn": data.get("kommunenavn"),
                    "fylkesnummer": fylkesnummer,
                    "fylkesnavn": data.get("fylkesnavn")
                }
            except Exception as e:
                logger.error(f"Error fetching Kommune info: {e}")
                return {}

    def _clean_address(self, address: str) -> str:
        """Normalize user-entered address text before Kartverket lookup."""
        if not address:
            return ""

        cleaned = address.replace("\r", "\n")
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if lines:
            preferred = next(
                (line for line in lines if "besøksadresse" in line.lower()),
                lines[0],
            )
            cleaned = preferred

        cleaned = re.sub(
            r"^(Besøksadresse|Postadresse|Adresse)[\s:]+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" ,")

    def _expand_abbreviations(self, address: str) -> str:
        """Expand common Norwegian street abbreviations to improve search hits."""
        if not address:
            return ""

        expanded = f" {address} "
        spaced_patterns = [
            (r"\bvn\b", "veien"),
            (r"\bvg\b", "vegen"),
            (r"\bgt\.?\b", "gate"),
            (r"\bgata\b", "gate"),
            (r"\bsgt\b", "s gate"),
            (r"\ball\b", "allé"),
            (r"\bpl\b", "plass"),
        ]
        compact_patterns = [
            (r"([A-Za-zÆØÅæøå]+)sgt\.?\b", r"\1s gate"),
            (r"([A-Za-zÆØÅæøå]+)gt\.?\b", r"\1 gate"),
            (r"([A-Za-zÆØÅæøå]+)vn\.?\b", r"\1veien"),
            (r"([A-Za-zÆØÅæøå]+)vg\.?\b", r"\1vegen"),
        ]

        for pattern, replacement in spaced_patterns:
            expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)
        expanded = expanded.strip()

        for pattern, replacement in compact_patterns:
            expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)

        return re.sub(r"\s{2,}", " ", expanded).strip(" ,")

    def _prepare_queries(
        self,
        address: str,
        city: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> tuple[list[str], Optional[str], Optional[str]]:
        """Build robust search variants and structured filters for Kartverket."""
        cleaned = self._clean_address(address)
        detected_city = city.strip() if isinstance(city, str) and city.strip() else None
        detected_postal = postal_code.strip() if isinstance(postal_code, str) and postal_code.strip() else None

        match = re.search(r",\s*(\d{4})\s+([A-Za-zÆØÅæøå .\-]+)$", cleaned)
        if match:
            detected_postal = detected_postal or match.group(1)
            detected_city = detected_city or match.group(2).strip()
            cleaned = cleaned[:match.start()].strip(" ,")
        elif "," in cleaned:
            left, right = [part.strip() for part in cleaned.rsplit(",", 1)]
            if right and re.fullmatch(r"[A-Za-zÆØÅæøå .\-]+", right):
                detected_city = detected_city or right
                cleaned = left

        cleaned = re.sub(
            r",?\s*\b(\d{1,2}\.?\s*etg|u\.?etg|h\d{4}|kld|leil\.?\s*\w+)\b.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r",?\s*(pb\.?|postboks)\s+.*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(\d+[A-Za-z]?)\s*(og|&)\s*\d+[A-Za-z]?.*$", r"\1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(\d+[A-Za-z]?)[/\-]\d+[A-Za-z]?.*$", r"\1", cleaned)
        cleaned = re.sub(r"(\d+[A-Za-z]?)[/\-][A-Za-z].*$", r"\1", cleaned)
        cleaned = re.sub(r"(\d+[A-Za-z]?),\s*[A-Za-z].*$", r"\1", cleaned)
        cleaned = cleaned.strip(" ,")

        expanded = self._expand_abbreviations(cleaned)
        queries: list[str] = []
        for candidate in [cleaned, expanded, self._clean_address(address)]:
            if candidate and candidate not in queries:
                queries.append(candidate)

        return queries, detected_city, detected_postal

    async def search_address(
        self,
        address: str,
        city: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> Optional[Dict[str, float]]:
        """
        Geocode address to (lat, lon).
        Uses: https://ws.geonorge.no/adresser/v1/sok
        """
        if not address:
            return None

        url = "https://ws.geonorge.no/adresser/v1/sok"
        queries, city_filter, postal_filter = self._prepare_queries(address, city, postal_code)

        import httpx
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in queries:
                filter_variants = []
                if city_filter or postal_filter:
                    filter_variants.append((city_filter, postal_filter))
                if city_filter:
                    filter_variants.append((city_filter, None))
                if postal_filter:
                    filter_variants.append((None, postal_filter))
                filter_variants.append((None, None))

                seen_filters = set()
                for current_city, current_postal in filter_variants:
                    filter_key = (current_city or "", current_postal or "")
                    if filter_key in seen_filters:
                        continue
                    seen_filters.add(filter_key)

                    params = {
                        "sok": query,
                        "treffPerSide": 1,
                        "asciiKompatibel": "true",
                    }
                    if current_city:
                        params["kommunenavn"] = current_city
                    if current_postal:
                        params["postnummer"] = current_postal

                    try:
                        resp = await client.get(url, params=params, headers=headers)
                        resp.raise_for_status()
                        data = resp.json()
                        addresses = data.get("adresser", [])

                        if addresses:
                            point = addresses[0].get("representasjonspunkt", {})
                            return {
                                "latitude": point.get("lat"),
                                "longitude": point.get("lon")
                            }
                    except Exception as e:
                        logger.error(f"Error geocoding address '{query}': {e}")
                        continue

        return None
    async def fetch_property_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Wrapper to fetch all relevant property data from Kartverket/Geonorge
        based on coordinates.
        """
        kommune_data = await self.get_kommune_from_point(latitude, longitude)
        # Could fetch altitude here if we had an endpoint
        
        return {
            "source_api": "kartverket",
            "latitude": latitude,
            "longitude": longitude,
            **kommune_data
        }

    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Wrapper for search_address to match test expectations.
        """
        coords = await self.search_address(address)
        if coords:
            return {
                "source_api": "kartverket",
                "address": address,
                "latitude": coords["latitude"],
                "longitude": coords["longitude"]
            }
        return {"error": "Address not found"}
