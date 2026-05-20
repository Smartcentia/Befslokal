from typing import Dict, Any, List, Optional
import asyncio
import logging
from app.services.external.api_clients.nve_client import NVEClient
from app.services.external.api_clients.kartverket_client import KartverketClient
from app.services.external.api_clients.miljodir_client import MiljodirClient

logger = logging.getLogger(__name__)

class ExternalRiskService:
    """
    Service that aggregates risk data from multiple external sources (NVE, Kartverket, Miljødirektoratet).
    Returns a unified risk assessment structure.
    """

    def __init__(self):
        self.nve = NVEClient()
        self.kartverket = KartverketClient()
        self.miljodir = MiljodirClient()

    async def _fetch_miljodir_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Helper to fetch all Miljødir and related environmental data in parallel.
        """
        try:
             # Existing Vannmiljø tasks
             water_task = self.miljodir.fetch_water_features(lat, lon)
             species_task = self.miljodir.fetch_species_registrations(lat, lon)
             medium_task = self.miljodir.fetch_medium_list()
             param_task = self.miljodir.fetch_parameter_list()
             
             # New tasks
             air_task = self.miljodir.fetch_air_quality(lat, lon)
             contam_task = self.miljodir.fetch_contaminated_sites(lat, lon)
             noise_task = self.miljodir.fetch_noise_data(lat, lon)
             
             # Run them all in parallel
             (w_res, s_res, m_list, p_list, 
              air_res, contam_res, noise_res) = await asyncio.gather(
                 water_task, species_task, medium_task, param_task,
                 air_task, contam_task, noise_task
             )
             
             # Map IDs to names for Vannmiljø
             resolved_species = self._resolve_vannmiljo_ids(s_res, m_list, p_list)
             resolved_water = self._resolve_vannmiljo_ids(w_res, m_list, p_list)
             
             return {
                 "water_features": resolved_water,
                 "species_registrations": resolved_species,
                 "water_features_count": len(w_res),
                 "species_count": len(s_res),
                 "air_quality": air_res,
                 "contaminated_sites": contam_res,
                 "noise_data": noise_res,
                 "contaminated_sites_count": len(contam_res),
                 "noise_events_count": len(noise_res)
             }
        except Exception as e:
            logger.error(f"Error fetching comprehensive Miljødir data: {e}")
            return {}

    def _resolve_vannmiljo_ids(self, rows: List[Dict], mediums: List[Dict], params: List[Dict]) -> List[Dict]:
        """
        Helper to map MediumID and ParameterID to human-readable names.
        """
        if not rows: return []
        
        m_map = {str(m.get("ID")): m.get("Navn") for m in mediums if m.get("ID")}
        p_map = {str(p.get("ID")): p.get("Navn") for p in params if p.get("ID")}
        
        resolved = []
        for row in rows:
            new_row = dict(row)
            mid = str(row.get("MediumID"))
            pid = str(row.get("ParameterID"))
            
            if mid in m_map:
                new_row["MediumNavn"] = m_map[mid]
            if pid in p_map:
                new_row["ParameterNavn"] = p_map[pid]
                
            resolved.append(new_row)
        return resolved

    async def assess_property_risk(
        self, 
        property_id: str, 
        latitude: float, 
        longitude: float, 
        risk_types: List[str] = ["all"]
    ) -> Dict[str, Any]:
        """
        Perform a comprehensive risk assessment for a property.
        """
        tasks = []
        
        # Determine what to fetch
        fetch_flood = "all" in risk_types or "flood" in risk_types
        fetch_landslide = "all" in risk_types or "geotechnical" in risk_types
        fetch_env = "all" in risk_types or "environmental" in risk_types or "biodiversity" in risk_types
        
        # 1. Flood Risk (NVE)
        if fetch_flood:
            tasks.append(self.nve.fetch_flood_risk(latitude, longitude))
        else:
            tasks.append(asyncio.sleep(0))
            
        # 2. Landslide/Geotech Risk (NVE)
        if fetch_landslide:
            tasks.append(self.nve.fetch_landslide_forecast(latitude, longitude))
        else:
            tasks.append(asyncio.sleep(0))
            
        # 3. Environmental Risk (Miljødirektoratet / NILU)
        if fetch_env:
            tasks.append(self._fetch_miljodir_data(latitude, longitude))
        else:
            tasks.append(asyncio.sleep(0))
            
        # Execute parallel
        results = await asyncio.gather(*tasks)
        
        flood_data = results[0] if fetch_flood and isinstance(results[0], dict) else {}
        landslide_data = results[1] if fetch_landslide and isinstance(results[1], dict) else {}
        env_data = results[2] if fetch_env and isinstance(results[2], dict) else {}

        # Calculate scores with status tracking
        flood_score, flood_status = self._calculate_flood_score(flood_data)
        geo_score, geo_status = self._calculate_geotech_score(landslide_data)
        env_score, env_status = self._calculate_env_score(env_data)

        # Build data_issues dict (only include sources that had errors)
        data_issues = {}
        if fetch_flood and flood_status == "error":
            data_issues["nve_flood"] = flood_data.get("_error", "API-feil")
        if fetch_landslide and geo_status == "error":
            data_issues["nve_landslide"] = landslide_data.get("_error", "API-feil")
        if fetch_env and env_status == "error":
            data_issues["miljodir"] = "Miljødirektorat-data utilgjengelig"

        # Calculate confidence: fraction of requested sources that returned real data
        statuses = []
        if fetch_flood: statuses.append(flood_status)
        if fetch_landslide: statuses.append(geo_status)
        if fetch_env: statuses.append(env_status)
        ok_count = sum(1 for s in statuses if s in ("ok", "no_data"))
        data_confidence = ok_count / len(statuses) if statuses else 1.0

        # Weighted average
        active_scores = []
        if fetch_flood: active_scores.append(flood_score)
        if fetch_landslide: active_scores.append(geo_score)
        if fetch_env: active_scores.append(env_score)

        overall = sum(active_scores) / len(active_scores) if active_scores else 0
        
        # Build environmental summary
        env_summary = "Ingen miljødata funnet."
        if env_data:
            details = []
            if env_data.get('water_features_count'): details.append(f"{env_data['water_features_count']} vannforekomster")
            if env_data.get('species_count'): details.append(f"{env_data['species_count']} artsregistreringer")
            if env_data.get('contaminated_sites_count'): details.append(f"{env_data['contaminated_sites_count']} forurensede lokaliteter")
            if env_data.get('noise_events_count'): details.append("Støyutsatt område (kartlagt)")
            
            air = env_data.get('air_quality', [])
            if air:
                 # Check for high values in NILU data
                 levels = [a.get('index') for a in air if a.get('index') is not None]
                 if levels and max(levels) > 2:
                      details.append("Mulig redusert luftkvalitet")
            
            if details:
                env_summary = "Faktorer identifisert: " + ", ".join(details)
            else:
                env_summary = "Nærområdet ser ut til å ha lav miljøbelastning basert på tilgjengelige data."
        
        return {
            "property_id": property_id,
            "overall_score": round(overall, 1),
            "data_confidence": round(data_confidence, 2),
            "data_issues": data_issues if data_issues else None,
            "recommendations": self._generate_recommendations(flood_score, geo_score, env_score),
            "flood_risk": {
                "score": flood_score,
                "status": flood_status,
                "data": flood_data.get("forecast", {}),
                "source": "NVE Flomvarsling"
            },
            "geotechnical_risk": {
                "score": geo_score,
                "status": geo_status,
                "data": landslide_data,
                "source": "NVE Jordskredvarsling"
            },
            "environmental_risk": {
                "score": env_score,
                "status": env_status,
                "data": env_data,
                "summary": env_summary,
                "source": "Miljødirektoratet (Vannmiljø, Grunnforurensning, Støy) & NILU (Luft)"
            }
        }

    def _calculate_flood_score(self, data: Dict[str, Any]):
        """Returns (score, status) where status is 'ok', 'no_data', or 'error'."""
        if not data:
            return 0, "no_data"
        if data.get("status") == "error":
            return 0, "error"
        max_level = 0
        warnings = data.get("forecast", {}).get("warnings", [])
        if not warnings and isinstance(data.get("warnings"), list):
             warnings = data.get("warnings")
        for w in warnings:
             lvl = int(w.get("activityLevel", 1))
             if lvl > max_level: max_level = lvl
        mapping = {0: 0, 1: 10, 2: 40, 3: 75, 4: 100}
        return mapping.get(max_level, 0), "ok"

    def _calculate_geotech_score(self, data: Dict[str, Any]):
        """Returns (score, status) where status is 'ok', 'no_data', or 'error'."""
        if not data:
            return 0, "no_data"
        if data.get("status") == "error":
            return 0, "error"
        max_level = 0
        warnings = data.get("warnings", [])
        for w in warnings:
             lvl = int(w.get("activityLevel", 1))
             if lvl > max_level: max_level = lvl
        mapping = {0: 0, 1: 10, 2: 40, 3: 75, 4: 100}
        return mapping.get(max_level, 0), "ok"

    def _calculate_env_score(self, data: Dict[str, Any]):
        """
        Calculate environmental risk score as a composite of biodiversity,
        air quality, soil contamination, and noise.
        Returns (score, status) where status is 'ok', 'no_data', or 'error'.
        """
        if not data:
            return 0, "no_data"
        if data.get("status") == "error":
            return 0, "error"

        score = 0
        
        # 1. Biodiversity (Vannmiljø) - Max 40 points
        species_count = data.get("species_count", 0)
        water_count = data.get("water_features_count", 0)
        bio_score = 0
        if species_count > 0: bio_score += 15
        if species_count > 10: bio_score += 15
        if water_count > 0: bio_score += 10
        score += min(bio_score, 40)
            
        # 2. Air Quality (NILU) - Max 20 points
        air = data.get('air_quality', [])
        if air:
            levels = [a.get('index') for a in air if a.get('index') is not None]
            if levels:
                max_air = max(levels)
                if max_air >= 2: score += 10 # Moderate
                if max_air >= 3: score += 10 # High
                
        # 3. Soil Contamination (Grunnforurensning) - Max 30 points
        contam_count = data.get('contaminated_sites_count', 0)
        if contam_count > 0: score += 15
        if contam_count > 5: score += 15
        
        # 4. Noise (Støy) - Max 10 points
        if data.get('noise_events_count', 0) > 0:
            score += 10
            
        return min(score, 100), "ok"

    def _generate_recommendations(self, flood: int, geo: int, env: int) -> List[str]:
        recs = []
        if flood >= 40:
            recs.append("Vurder flomsikringstiltak. Overvåk NVE varsler.")
        if geo >= 40:
            recs.append("Grunnundersøkelse anbefales pga skredfare/grunnforhold.")
        
        if env >= 30:
            recs.append("Vurder miljørisiko. Sjekk detaljerte kart for støy, luft og grunnforurensning.")
        if env >= 60:
            recs.append("Høy miljøbelastning eller strengt naturvern. Grundig miljøteknisk undersøkelse anbefales.")
            
        if not recs:
            recs.append("Ingen umiddelbare tiltak nødvendig basert på offentlige data.")
            
        return recs
