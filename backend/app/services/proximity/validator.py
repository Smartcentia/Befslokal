"""
Proximity Requirements Validator for Child Welfare Institutions.

Basert på: Krav til barnevernsinstitusjoner og forsvarlighetskravet i barnevernsloven § 1-7
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import ProximityService, Property
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ProximityRequirementsValidator:
    """Validerer om en eiendom oppfyller proximity-krav for barnevernsinstitusjoner."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = self._load_requirements()
        
    def _load_requirements(self) -> dict:
        """Laster proximity requirements fra YAML-fil."""
        config_path = Path(__file__).parent.parent / "config" / "proximity_requirements.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Proximity requirements config ikke funnet: {config_path}")
            return {}
        except Exception as e:
            logger.error(f"Feil ved lasting av proximity requirements: {e}")
            return {}
    
    async def validate_property(
        self,
        property_id: str,
        institution_type: Optional[str] = None,
        age_group: Optional[str] = None
    ) -> Dict:
        """
        Validerer om en eiendom oppfyller proximity-kravene.
        
        Args:
            property_id: UUID for eiendommen
            institution_type: Type institusjon (atferd, omsorg, akutt) - optional
            age_group: Aldersgruppe (age_13_15, age_16_18, age_18_20) - optional
            
        Returns:
            Dict med:
                - score: Accessibility score (0-100)
                - risk_level: "low", "medium" eller "high"
                - critical_services: Status for kritiske tjenester
                - important_services: Status for viktige tjenester
                - supportive_services: Status for støttende tjenester
                - missing_services: Liste over manglende tjenester
                - violations: Liste over krav som ikke oppfylles
                - recommendations: Anbefalinger for forbedring
        """
        # Hent proximity services for eiendommen
        services = await self._get_proximity_services(property_id)
        
        if not services:
            return {
                "score": 0,
                "risk_level": "high",
                "error": "Ingen proximity services funnet for denne eiendommen",
                "critical_services": {},
                "important_services": {},
                "supportive_services": {},
                "missing_services": [],
                "violations": ["Ingen proximity data tilgjengelig"],
                "recommendations": ["Kjør proximity services refresh for denne eiendommen"]
            }
        
        # Bygg service map (type -> nærmeste service)
        service_map = self._build_service_map(services)
        
        # Valider kritiske tjenester
        critical_result = self._validate_critical_services(service_map, institution_type)
        
        # Valider viktige tjenester
        important_result = self._validate_important_services(service_map)
        
        # Valider støttende tjenester
        supportive_result = self._validate_supportive_services(service_map)
        
        # Beregn total score
        score = self._calculate_score(critical_result, important_result, supportive_result)
        
        # Bestem risk level
        risk_level = self._determine_risk_level(score)
        
        # Generer anbefalinger
        recommendations = self._generate_recommendations(
            critical_result, important_result, supportive_result, institution_type, age_group
        )
        
        # Finn violations (kritiske krav som ikke oppfylles)
        violations = critical_result.get("violations", [])
        
        # Liste over alle manglende tjenester
        missing_services = []
        missing_services.extend(critical_result.get("missing", []))
        missing_services.extend(important_result.get("missing", []))
        missing_services.extend(supportive_result.get("missing", []))
        
        return {
            "score": round(score, 1),
            "risk_level": risk_level,
            "critical_services": critical_result.get("services", {}),
            "important_services": important_result.get("services", {}),
            "supportive_services": supportive_result.get("services", {}),
            "missing_services": missing_services,
            "violations": violations,
            "recommendations": recommendations,
            "metadata": {
                "total_services": len(services),
                "evaluated_at": "now",
                "institution_type": institution_type,
                "age_group": age_group
            }
        }
    
    async def _get_proximity_services(self, property_id: str) -> List[ProximityService]:
        """Henter alle proximity services for en eiendom."""
        stmt = select(ProximityService).where(ProximityService.property_id == property_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    def _build_service_map(self, services: List[ProximityService]) -> Dict[str, ProximityService]:
        """
        Bygger map av service type til nærmeste service.
        
        Returns:
            Dict[service_type, ProximityService] med nærmeste av hver type
        """
        service_map = {}
        for service in services:
            existing = service_map.get(service.service_type)
            if not existing or service.distance_meters < existing.distance_meters:
                service_map[service.service_type] = service
        return service_map
    
    def _validate_critical_services(
        self,
        service_map: Dict[str, ProximityService],
        institution_type: Optional[str] = None
    ) -> Dict:
        """Validerer kritiske tjenester mot krav."""
        if not self.requirements:
            return {"services": {}, "missing": [], "violations": [], "score": 0}
        
        critical_req = self.requirements.get("critical_services", {})
        
        # Hvis institution_type er spesifisert, merge med spesifikke krav
        if institution_type and "institution_types" in self.requirements:
            inst_reqs = self.requirements["institution_types"].get(institution_type, {})
            if "critical_services" in inst_reqs:
                # Override med mer strenge krav
                critical_req = {**critical_req, **inst_reqs["critical_services"]}
        
        services = {}
        missing = []
        violations = []
        total_critical = len(critical_req)
        met_critical = 0
        
        for service_type, requirements in critical_req.items():
            max_distance = requirements.get("max_distance_meters", float('inf'))
            reason = requirements.get("reason", "")
            description = requirements.get("description", service_type)
            
            if service_type in service_map:
                service = service_map[service_type]
                distance = service.distance_meters
                is_within_limit = distance <= max_distance
                
                if is_within_limit:
                    met_critical += 1
                else:
                    violations.append({
                        "service_type": service_type,
                        "description": description,
                        "reason": reason,
                        "required_max": max_distance,
                        "actual_distance": distance,
                        "message": f"{description} er {distance}m unna, maks tillatt er {max_distance}m"
                    })
                
                services[service_type] = {
                    "name": service.service_name,
                    "distance_meters": distance,
                    "max_allowed_meters": max_distance,
                    "within_limit": is_within_limit,
                    "reason": reason,
                    "address": service.address
                }
            else:
                missing.append({
                    "service_type": service_type,
                    "description": description,
                    "reason": reason,
                    "max_distance_meters": max_distance
                })
                violations.append({
                    "service_type": service_type,
                    "description": description,
                    "reason": reason,
                    "message": f"{description} mangler fullstendig"
                })
        
        # Sjekk minimum_critical_services regel
        validation_rules = self.requirements.get("validation_rules", {})
        min_required = validation_rules.get("minimum_critical_services", 3)
        
        if met_critical < min_required:
            violations.append({
                "rule": "minimum_critical_services",
                "message": f"Kun {met_critical} av {total_critical} kritiske tjenester oppfyller krav. Minimum er {min_required}.",
                "severity": "critical"
            })
        
        # Beregn score (prosentandel oppfylt)
        score = (met_critical / total_critical * 100) if total_critical > 0 else 0
        
        return {
            "services": services,
            "missing": missing,
            "violations": violations,
            "score": score,
            "met": met_critical,
            "total": total_critical
        }
    
    def _validate_important_services(self, service_map: Dict[str, ProximityService]) -> Dict:
        """Validerer viktige tjenester mot anbefalte krav."""
        if not self.requirements:
            return {"services": {}, "missing": [], "score": 0}
        
        important_req = self.requirements.get("important_services", {})
        services = {}
        missing = []
        total_important = len(important_req)
        met_important = 0
        
        for service_type, requirements in important_req.items():
            recommended_max = requirements.get("recommended_max_distance", float('inf'))
            reason = requirements.get("reason", "")
            description = requirements.get("description", service_type)
            
            if service_type in service_map:
                service = service_map[service_type]
                distance = service.distance_meters
                is_recommended = distance <= recommended_max
                
                if is_recommended:
                    met_important += 1
                
                services[service_type] = {
                    "name": service.service_name,
                    "distance_meters": distance,
                    "recommended_max_meters": recommended_max,
                    "within_recommended": is_recommended,
                    "reason": reason,
                    "address": service.address
                }
            else:
                missing.append({
                    "service_type": service_type,
                    "description": description,
                    "reason": reason,
                    "recommended_max_distance": recommended_max
                })
        
        score = (met_important / total_important * 100) if total_important > 0 else 0
        
        return {
            "services": services,
            "missing": missing,
            "score": score,
            "met": met_important,
            "total": total_important
        }
    
    def _validate_supportive_services(self, service_map: Dict[str, ProximityService]) -> Dict:
        """Validerer støttende tjenester."""
        if not self.requirements:
            return {"services": {}, "missing": [], "score": 0}
        
        supportive_req = self.requirements.get("supportive_services", {})
        services = {}
        missing = []
        total_supportive = len(supportive_req)
        met_supportive = 0
        
        for service_type, requirements in supportive_req.items():
            recommended_max = requirements.get("recommended_max_distance", float('inf'))
            reason = requirements.get("reason", "")
            description = requirements.get("description", service_type)
            
            if service_type in service_map:
                service = service_map[service_type]
                distance = service.distance_meters
                is_recommended = distance <= recommended_max
                
                if is_recommended:
                    met_supportive += 1
                
                services[service_type] = {
                    "name": service.service_name,
                    "distance_meters": distance,
                    "recommended_max_meters": recommended_max,
                    "within_recommended": is_recommended,
                    "reason": reason,
                    "address": service.address
                }
            else:
                missing.append({
                    "service_type": service_type,
                    "description": description,
                    "reason": reason
                })
        
        score = (met_supportive / total_supportive * 100) if total_supportive > 0 else 0
        
        return {
            "services": services,
            "missing": missing,
            "score": score,
            "met": met_supportive,
            "total": total_supportive
        }
    
    def _calculate_score(
        self,
        critical_result: Dict,
        important_result: Dict,
        supportive_result: Dict
    ) -> float:
        """Beregner total accessibility score (0-100)."""
        if not self.requirements:
            return 0.0
        
        validation_rules = self.requirements.get("validation_rules", {})
        scoring = validation_rules.get("scoring", {})
        
        critical_weight = scoring.get("critical_weight", 0.6)
        important_weight = scoring.get("important_weight", 0.3)
        supportive_weight = scoring.get("supportive_weight", 0.1)
        
        critical_score = critical_result.get("score", 0)
        important_score = important_result.get("score", 0)
        supportive_score = supportive_result.get("score", 0)
        
        total_score = (
            critical_score * critical_weight +
            important_score * important_weight +
            supportive_score * supportive_weight
        )
        
        return total_score
    
    def _determine_risk_level(self, score: float) -> str:
        """Bestemmer risk level basert på score."""
        if not self.requirements:
            return "unknown"
        
        validation_rules = self.requirements.get("validation_rules", {})
        thresholds = validation_rules.get("risk_thresholds", {})
        
        high_threshold = thresholds.get("high_risk", 40)
        medium_threshold = thresholds.get("medium_risk", 60)
        
        if score < high_threshold:
            return "high"
        elif score < medium_threshold:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self,
        critical_result: Dict,
        important_result: Dict,
        supportive_result: Dict,
        institution_type: Optional[str],
        age_group: Optional[str]
    ) -> List[str]:
        """Genererer anbefalinger basert på valideringsresultat."""
        recommendations = []
        
        # Kritiske mangler
        critical_missing = critical_result.get("missing", [])
        if critical_missing:
            recommendations.append(
                f"KRITISK: {len(critical_missing)} kritiske tjenester mangler helt. "
                "Dette kan være brudd på forsvarlighetskravet."
            )
            for missing in critical_missing[:3]:  # Top 3
                recommendations.append(
                    f"  • {missing['description']}: {missing['reason']}"
                )
        
        # Kritiske violations (for langt unna)
        violations = [v for v in critical_result.get("violations", []) if "actual_distance" in v]
        if violations:
            recommendations.append(
                f"VIKTIG: {len(violations)} kritiske tjenester er utenfor maksimal avstand."
            )
            for violation in violations[:2]:  # Top 2
                recommendations.append(
                    f"  • {violation['description']}: {violation['actual_distance']}m "
                    f"(maks {violation['required_max']}m)"
                )
        
        # Viktige tjenester
        important_missing = important_result.get("missing", [])
        if important_missing:
            recommendations.append(
                f"Bør forbedres: {len(important_missing)} viktige tjenester mangler."
            )
        
        # Positiv feedback hvis score er høy
        score = self._calculate_score(critical_result, important_result, supportive_result)
        if score >= 80:
            recommendations.append(
                "✓ Eiendommen har god tilgjengelighet til nødvendige tjenester."
            )
        
        # Ingen recommendations
        if not recommendations:
            recommendations.append("Ingen spesifikke anbefalinger.")
        
        return recommendations


async def validate_property_proximity(
    db: AsyncSession,
    property_id: str,
    institution_type: Optional[str] = None,
    age_group: Optional[str] = None
) -> Dict:
    """
    Convenience function for å validere proximity requirements for en eiendom.
    
    Args:
        db: Database session
        property_id: UUID for eiendommen
        institution_type: Type institusjon (atferd, omsorg, akutt)
        age_group: Aldersgruppe (age_13_15, age_16_18, age_18_20)
        
    Returns:
        Validation result dict
    """
    validator = ProximityRequirementsValidator(db)
    return await validator.validate_property(property_id, institution_type, age_group)
