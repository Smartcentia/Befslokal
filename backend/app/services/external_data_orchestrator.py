from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.external.api_clients.nve_client import NVEClient
from app.services.external.api_clients.kartverket_client import KartverketClient
from app.services.external.api_clients.lovdata_client import LovdataClient
from app.models.external_api_data import ExternalApiData
from app.core.config import settings
import logging
import datetime
import uuid

logger = logging.getLogger(__name__)

class ExternalDataOrchestrator:
    """
    Orchestrates fetching data from multiple external sources and handles persistence.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize clients (optionally getting keys from settings)
        self.nve = NVEClient(api_key=getattr(settings, "NVE_API_KEY", None))
        self.kartverket = KartverketClient()
        self.lovdata = LovdataClient()

    async def fetch_risk_data(self, latitude: float, longitude: float, property_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch combined risk data (NVE Stations + Flood Forecast).
        Handles persistence in the external_api_data table.
        """
        import asyncio
        
        # 1. Check if we have fresh data in the DB (Fast path)
        cached_data = await self._get_cached_data(property_id)
        if cached_data:
            logger.info(f"Using cached risk data for property {property_id}")
            return cached_data

        results = {}
        fetch_errors = {}

        # 2. Parallel Fetch: Kartverket (Geo) + NVE (Stations)
        try:
            geo_task = self.kartverket.get_kommune_from_point(latitude, longitude)
            stations_task = self.nve.fetch_nearby_stations(latitude, longitude)

            geo_info, stations = await asyncio.gather(geo_task, stations_task)

            results["geo_info"] = geo_info
            results["nve_stations"] = stations

            # 3. Fetch Flood Forecast (Dependent on Geo Info)
            fylkesnummer = geo_info.get("fylkesnummer")
            if fylkesnummer:
                forecast = await self.nve.fetch_flood_forecast(latitude, longitude, county_code=fylkesnummer)
                results["flood_forecast"] = forecast
            else:
                results["flood_forecast"] = {"status": "skipped", "reason": "No fylkesnummer found"}
                fetch_errors["geo_lookup"] = "Fant ikke fylkesnummer for koordinatene"

        except Exception as e:
            logger.error(f"Error fetching external data: {e}")
            if "geo_info" not in results: results["geo_info"] = {}
            if "nve_stations" not in results: results["nve_stations"] = []
            results["flood_forecast"] = {"status": "error", "reason": str(e)}
            fetch_errors["nve_flood"] = str(e)

        results["_fetch_errors"] = fetch_errors

        # 4. Store in DB if property_id is provided
        if property_id:
            await self._save_cache_data(property_id, results)
            
        return results

    async def _get_cached_data(self, property_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data if it exists and is not expired.
        """
        if not property_id:
            return None
            
        try:
            prop_uuid = str(uuid.UUID(property_id))
            # Find latest entry for this property that hasn't expired
            query = select(ExternalApiData).where(
                ExternalApiData.entity_id == prop_uuid,
                ExternalApiData.entity_type == "property",
                (ExternalApiData.expires_at == None) | (ExternalApiData.expires_at > datetime.datetime.now(datetime.timezone.utc))
            ).order_by(ExternalApiData.fetched_at.desc()).limit(1)
            
            result = await self.db.execute(query)
            cached = result.scalar_one_or_none()
            if cached:
                return cached.data
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            
        return None

    async def _save_cache_data(self, property_id: str, data: Dict[str, Any]):
        """
        Save results to ExternalApiData table.
        """
        try:
            prop_uuid = str(uuid.UUID(property_id))
            new_cache = ExternalApiData(
                api_data_id=uuid.uuid4(),
                source_api="aggregated_risk",
                entity_type="property",
                entity_id=prop_uuid,
                data=data,
                fetched_at=datetime.datetime.now(datetime.timezone.utc),
                expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
            )
            self.db.add(new_cache)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
