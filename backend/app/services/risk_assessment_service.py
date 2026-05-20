from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import base as models

class RiskAssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _categorize_risk(self, score: float) -> str:
        if score <= 20:
            return "low"
        elif score <= 50:
            return "medium"
        elif score <= 75:
            return "high"
        else:
            return "critical"

    def _calculate_distance_risk(self, distance: Optional[float]) -> int:
        """Calculate distance risk score (1-10). Handles None/invalid values."""
        if distance is None:
            return 10  # Unknown distance = high risk
        try:
            dist = int(distance)
        except (TypeError, ValueError):
            return 10
        # Based on test: 500->1, 1500->3, 3000->6, 8000->8, 15000->10
        if dist <= 500: return 1
        if dist <= 1500: return 3
        if dist <= 3000: return 6
        if dist <= 8000: return 8
        return 10

    def _calculate_time_risk(self, minutes: Optional[float]) -> int:
        """Calculate time risk score (1-10). Handles None/invalid values."""
        if minutes is None:
            return 10  # Unknown time = high risk
        try:
            mins = int(minutes)
        except (TypeError, ValueError):
            return 10
        # Based on test: 3->1, 8->3, 15->6, 25->8, 40->10
        if mins <= 5: return 1
        if mins <= 10: return 3
        if mins <= 20: return 6
        if mins <= 30: return 8
        return 10

    async def calculate_accessibility_risk(self, property_id: UUID) -> Dict[str, Any]:
        # Fetch proximity services
        stmt = select(models.ProximityService).filter(models.ProximityService.property_id == property_id)
        result = await self.db.execute(stmt)
        services = result.scalars().all()

        if not services:
            return {
                "risk_score": 100,
                "risk_category": "critical",
                "message": "Ingen proximity data funnet",
                "factors": []
            }

        total_risk = 0
        count = 0
        factors = []

        for service in services:
            dist_risk = self._calculate_distance_risk(service.distance_meters)
            time_risk = self._calculate_time_risk(service.travel_time_minutes)
            
            # Average them for this service
            service_risk = (dist_risk + time_risk) / 2
            
            # Normalize to 0-100 scale. Returns 1-10. So * 10?
            service_risk_100 = service_risk * 10
            
            total_risk += service_risk_100
            count += 1
            
            # Safe formatting with None handling
            dist_str = f"{service.distance_meters}m" if service.distance_meters is not None else "N/A"
            time_str = f"{service.travel_time_minutes}min" if service.travel_time_minutes is not None else "N/A"
            
            factors.append({
                "service_type": service.service_type or "unknown",
                "risk_score": service_risk_100,
                "description": f"Distance: {dist_str}, Time: {time_str}"
            })

        avg_risk = total_risk / count if count > 0 else 100
        
        return {
            "risk_score": avg_risk,
            "risk_category": self._categorize_risk(avg_risk),
            "factors": factors, # Use as risk factors
            "message": "Accessibility analysed"
        }

    async def create_risk_assessment(self, property_id: UUID, methodology: str = "MCDA") -> models.RiskAssessment:
        risk_data = await self.calculate_accessibility_risk(property_id)
        
        risk_score = risk_data["risk_score"]
        risk_category = risk_data["risk_category"]
        
        assessment = models.RiskAssessment(
            property_id=property_id,
            methodology=methodology,
            overall_risk_score=risk_score,
            risk_category=risk_category,
            assessment_date=datetime.utcnow()
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        
        # Create factors
        for factor in risk_data.get("factors", []):
            rf = models.RiskFactor(
                assessment_id=assessment.assessment_id,
                category="proximity",
                factor_name=factor.get("service_type", "accessibility"),
                calculated_score=factor["risk_score"],
                data_source=factor.get("description"),
                weight=1.0 # Default
            )
            self.db.add(rf)
            
        await self.db.commit()
        return assessment

    async def get_latest_assessment(self, property_id: UUID) -> Optional[models.RiskAssessment]:
        stmt = select(models.RiskAssessment)\
            .filter(models.RiskAssessment.property_id == property_id)\
            .order_by(models.RiskAssessment.assessment_date.desc())\
            .limit(1)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_assessment_history(self, property_id: UUID, limit: int = 10) -> List[models.RiskAssessment]:
        stmt = select(models.RiskAssessment)\
            .filter(models.RiskAssessment.property_id == property_id)\
            .order_by(models.RiskAssessment.assessment_date.desc())\
            .limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
