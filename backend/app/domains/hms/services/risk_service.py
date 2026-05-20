from typing import Dict, Any, List, Optional
import random
import datetime
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.domains.hms.models.risk import RiskAssessment
from app.domains.core.models.property import Property


logger = logging.getLogger(__name__)

class RiskService:
    """
    Calculates Risk Assessment per Location.
    Uses 'Real' data to determine risk factors.
    """
    
    @staticmethod
    async def calculate_risk_for_property(prop_id: str, db: AsyncSession) -> Dict[str, Any]:
        try:
            uuid_obj = UUID(prop_id)
            query = select(Property).filter(Property.property_id == uuid_obj)
            result = await db.execute(query)
            prop = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching property {prop_id}: {e}")
            return None

        if not prop:
            logger.warning(f"Property {prop_id} not found in DB.")
            return None
        
        logger.info(f"Calculating risk for property: {prop.address}")

        # --- EXTRACT EXTERNAL RISK FACTORS (SEPARATE SCORE) ---
        external_risk_score = 0
        external_factors = []

        # 1. Base Score based on Building Year (Older = Higher Risk)
        ext = prop.external_data or {}
        year_built = ext.get("year_built", 2000)
        current_year = datetime.datetime.now().year
        age = current_year - year_built
        
        # Age adds to EXTERNAL/ASSET risk, not operational risk
        external_risk_score += (max(0, age) * 0.5) 
        if age > 40:
            external_factors.append(f"Høy alder på bygningsmasse ({age} år)")

        # 2. Size factor
        sqm = ext.get("sqm", 0)
        if sqm > 10000:
            external_risk_score += 10
            external_factors.append("Stort areal øker kompleksitet")

        # 3. External factors from Orchestrator (Flood, Slide, etc)
        from app.services.external_data_orchestrator import ExternalDataOrchestrator
        orchestrator = ExternalDataOrchestrator(db)
        
        data_confidence = 1.0
        data_issues = {}

        if not prop.latitude or not prop.longitude:
            data_confidence = 0.0
            data_issues["coordinates"] = "Eiendom mangler koordinater (lat/lon)"

        if prop.latitude and prop.longitude:
            try:
                ext_risk = await orchestrator.fetch_risk_data(
                    prop.latitude,
                    prop.longitude,
                    property_id=str(prop.property_id)
                )
                
                # NVE Stations
                nve_stations = ext_risk.get("nve_stations", [])
                if nve_stations:
                    closest = nve_stations[0].get("distance_km", 999)
                    if closest < 1.0:
                        external_risk_score += 15
                        external_factors.append(f"Nærhet til vannvei (NVE stasjon {closest}km unna)")

                # Collect fetch errors from orchestrator for confidence tracking
                fetch_errors = ext_risk.get("_fetch_errors", {})
                if fetch_errors:
                    data_issues.update(fetch_errors)

                # Flood Forecast
                flood_forecast = ext_risk.get("flood_forecast", {})
                flood_status = flood_forecast.get("status") if isinstance(flood_forecast, dict) else None
                if flood_status == "error":
                    data_issues["nve_flood"] = flood_forecast.get("reason", "NVE API-feil")
                    data_confidence = max(0.0, data_confidence - 0.5)
                elif flood_status == "skipped":
                    data_issues["nve_flood"] = flood_forecast.get("reason", "Flomvarsel ikke hentet")
                    data_confidence = max(0.0, data_confidence - 0.3)

                if isinstance(flood_forecast, list) and len(flood_forecast) > 0:
                    top_level = flood_forecast[0].get("warningLevel", 0)
                    if top_level > 1:
                        external_risk_score += 25
                        external_factors.append(f"Aktivt flomvarsel (Nivå {top_level})")
                elif isinstance(flood_forecast, dict) and flood_forecast.get("warningLevel"):
                     level = flood_forecast.get("warningLevel", 0)
                     if level > 1:
                        external_risk_score += 25
                        external_factors.append(f"Aktivt flomvarsel (Nivå {level})")
            except Exception as e:
                logger.error(f"Error fetching external risk data for property {prop_id}: {e}")
                data_issues["external_fetch"] = str(e)
                data_confidence = 0.0

        external_risk_score = min(100, int(external_risk_score))


        # --- CALCULATE MAIN RISK SCORE (DEVIATIONS & MEASURES) ---
        # Risk Score is now purely based on operational deviations and missing measures
        deviation_score = 0
        operational_factors = []
        
        try:
            from app.domains.hms.models.internal_control import InternalControlCase
            
            # Count Open Deviations
            # Assuming 'status' field string or enum. 
            # Using raw SQL or specific filter provided we don't have the exact Enum handy in this context, 
            # but 'open', 'tiltak', 'analyse' imply active. 'lukket' is closed.
            stmt = select(InternalControlCase).filter(
                InternalControlCase.property_id == uuid_obj,
                InternalControlCase.status != 'closed',
                InternalControlCase.status != 'lukket' 
            )
            res = await db.execute(stmt)
            open_cases = res.scalars().all()
            
            num_deviations = len(open_cases)
            
            if num_deviations > 0:
                deviation_score += (num_deviations * 10) # 10 points per deviation
                operational_factors.append(f"{num_deviations} krevende avvik registrert")
                
                # Check for "Missing Measures" (Manglende tiltak)
                # We approximate this by checking cases in 'Tiltak' state that are overdue or just count them specifically
                # For now, let's say cases in 'Tiltak' state add extra urgency
                cases_in_measures = [c for c in open_cases if c.process_state == 'Tiltak']
                if cases_in_measures:
                    deviation_score += (len(cases_in_measures) * 10) # Extra 10 points if in measure phase (implementation risk)
                    operational_factors.append(f"{len(cases_in_measures)} avvik venter på tiltaksgjennomføring")

        except Exception as e:
            logger.error(f"Error checking deviations: {e}")
            operational_factors.append("Feil ved henting av avviksdata")

        
        # Normalize Main Score
        final_risk_score = min(100, deviation_score)
            
        status = "low"
        if final_risk_score > 75:
            status = "critical"
        elif final_risk_score > 40:
            status = "high"
        elif final_risk_score > 0:
            status = "moderate"
            
        # Derive assessment_status from confidence
        if not prop.latitude or not prop.longitude:
            assessment_status = "no_coordinates"
        elif data_confidence >= 0.8:
            assessment_status = "complete"
        elif data_confidence >= 0.3:
            assessment_status = "partial"
        else:
            assessment_status = "failed"

        return {
            "property_id": prop_id,
            "property_name": prop.name if hasattr(prop, 'name') and prop.name else prop.address,
            "risk_score": final_risk_score,
            "status": status,
            "factors": operational_factors,
            "external_risk": {
                "score": external_risk_score,
                "factors": external_factors
            },
            "data_confidence": round(data_confidence, 2),
            "data_issues": data_issues if data_issues else None,
            "assessment_status": assessment_status,
            "assessed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }



    @staticmethod
    async def batch_update_risks(db: AsyncSession) -> Dict[str, Any]:
        """
        Updates risk for ALL properties in DB using PARALLEL execution.
        """
        import asyncio
        from app.db.session import SessionLocal
        from app.domains.hms.models.risk import RiskFactor
        
        # 1. Get all Property IDs first (using the passed session is fine for a read)
        result = await db.execute(select(Property.property_id))
        prop_ids = result.scalars().all()
        
        # 2. Worker setup
        # Use a smaller Semaphore (e.g. 4) to prevent DB connection pool starvation. 
        # The pool_size is 3 + max_overflow 7 = 10. 
        sem = asyncio.Semaphore(4) 
        results = []
        
        async def process_property_safe(pid):
            async with sem:
                try:
                    # Create a NEW session for this task to avoid asyncpg concurrency issues on a single connection
                    async with SessionLocal() as session:
                        # Fetch previous assessment to compare
                        from app.domains.hms.models.risk import RiskAssessment
                        query_prev = select(RiskAssessment).filter(RiskAssessment.property_id == pid).order_by(RiskAssessment.assessment_date.desc()).limit(1)
                        res_prev = await session.execute(query_prev)
                        prev_assessment = res_prev.scalar_one_or_none()
                        old_score = prev_assessment.overall_risk_score if prev_assessment else None
                        old_status = prev_assessment.risk_category if (prev_assessment and prev_assessment.risk_category) else "Ingen tidligere data"

                        risk_data = await RiskService.calculate_risk_for_property(str(pid), session)
                        
                        if risk_data:
                            # Create and Persist RiskAssessment
                            new_assessment = RiskAssessment(
                                property_id=pid,
                                risk_category=risk_data["status"],
                                overall_risk_score=risk_data["risk_score"],
                                notes=", ".join(risk_data["factors"]),
                                assessment_date=datetime.datetime.now(datetime.timezone.utc),
                                assessed_by="Batch Processor",
                                methodology="Automated Batch v2",
                                data_confidence=risk_data.get("data_confidence"),
                                data_issues=risk_data.get("data_issues"),
                                assessment_status=risk_data.get("assessment_status"),
                            )
                            session.add(new_assessment)
                            await session.flush()

                            # Persist Operational Factors
                            for theory in risk_data.get("factors", []):
                                rf = RiskFactor(
                                    assessment_id=new_assessment.assessment_id,
                                    category="operational",
                                    factor_name=theory,
                                    calculated_score=10.0,
                                    data_source="InternalControl",
                                    weight=1.0
                                )
                                session.add(rf)

                            # Persist External Factors
                            ext_data = risk_data.get("external_risk", {})
                            ext_score = ext_data.get("score", 0)
                            for ext_f in ext_data.get("factors", []):
                                rf_ext = RiskFactor(
                                    assessment_id=new_assessment.assessment_id,
                                    category="external",
                                    factor_name=ext_f,
                                    calculated_score=ext_score,
                                    data_source="ExternalOrchestrator",
                                    weight=1.0
                                )
                                session.add(rf_ext)
                            
                            await session.commit()
                            
                            # Return detailed result for the report
                            all_factors = risk_data.get("factors", []) + ext_data.get("factors", [])
                            return {
                                "property_id": str(pid),
                                "property_name": risk_data.get("property_name", str(pid)),
                                "old_score": old_score,
                                "new_score": risk_data["risk_score"],
                                "old_status": old_status,
                                "new_status": risk_data["status"],
                                "factors": all_factors
                            }
                except Exception as e:
                    logger.error(f"Error processing property {pid}: {e}")
                    return None
        
        # 3. Launch tasks
        tasks = [process_property_safe(pid) for pid in prop_ids]
        completed_results = await asyncio.gather(*tasks)
        
        # Filter out Nones
        successful = [r for r in completed_results if r is not None]

        return {
            "processed": len(successful),
            "total_attempted": len(prop_ids),
            "status": "Completed",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "details": successful
        }

risk_service = RiskService()
