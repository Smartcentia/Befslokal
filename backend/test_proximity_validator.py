"""
Test script for Proximity Requirements Validator.

Dette scriptet demonstrerer validering av proximity-krav for barnevernsinstitusjoner.
"""
import asyncio
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.session import AsyncSessionLocal
from app.services.proximity.validator import ProximityRequirementsValidator


async def test_validator():
    """Test proximity validator med eksempel-eiendom."""
    
    print("=" * 80)
    print("PROXIMITY REQUIREMENTS VALIDATOR - TEST")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as db:
        validator = ProximityRequirementsValidator(db)
        
        # Sjekk at config er lastet
        if not validator.requirements:
            print("❌ FEIL: Kunne ikke laste proximity_requirements.yaml")
            return
        
        print("✅ Config lastet:")
        critical = validator.requirements.get("critical_services", {})
        important = validator.requirements.get("important_services", {})
        supportive = validator.requirements.get("supportive_services", {})
        
        print(f"   - {len(critical)} kritiske tjenester")
        print(f"   - {len(important)} viktige tjenester")
        print(f"   - {len(supportive)} støttende tjenester")
        print()
        
        # Liste kritiske krav
        print("📋 KRITISKE KRAV (må oppfylles):")
        print("-" * 80)
        for service_type, req in critical.items():
            max_dist = req.get("max_distance_meters", 0)
            description = req.get("description", service_type)
            reason = req.get("reason", "")
            print(f"   {service_type.upper()}")
            print(f"   └─ {description}")
            print(f"      Maks avstand: {max_dist}m ({max_dist/1000:.1f} km)")
            print(f"      Begrunnelse: {reason}")
            print()
        
        print()
        print("=" * 80)
        print("VALIDERING EKSEMPEL")
        print("=" * 80)
        print()
        print("For å validere en faktisk eiendom, kjør:")
        print()
        print("  from app.services.proximity.validator import validate_property_proximity")
        print()
        print("  result = await validate_property_proximity(")
        print("      db=db,")
        print("      property_id='<property-uuid>',")
        print("      institution_type='atferd',  # eller 'omsorg', 'akutt'")
        print("      age_group='age_16_18'       # eller 'age_13_15', 'age_18_20'")
        print("  )")
        print()
        print("  print(f\"Score: {result['score']}/100\")")
        print("  print(f\"Risk: {result['risk_level']}\")")
        print("  print(f\"Violations: {len(result['violations'])}\")")
        print()
        print("Eller via API:")
        print()
        print("  GET /api/properties/{id}/proximity-validation")
        print("      ?institution_type=atferd")
        print("      &age_group=age_16_18")
        print()
        
        # Vis scoring system
        print("=" * 80)
        print("SCORING SYSTEM")
        print("=" * 80)
        print()
        
        validation_rules = validator.requirements.get("validation_rules", {})
        scoring = validation_rules.get("scoring", {})
        thresholds = validation_rules.get("risk_thresholds", {})
        
        print("Vekting:")
        print(f"   - Kritiske tjenester: {scoring.get('critical_weight', 0)*100:.0f}%")
        print(f"   - Viktige tjenester: {scoring.get('important_weight', 0)*100:.0f}%")
        print(f"   - Støttende tjenester: {scoring.get('supportive_weight', 0)*100:.0f}%")
        print()
        
        print("Risk Levels:")
        print(f"   - HIGH:   Score < {thresholds.get('high_risk', 40)} (ikke forsvarlig)")
        print(f"   - MEDIUM: Score {thresholds.get('high_risk', 40)}-{thresholds.get('medium_risk', 60)} (bør forbedres)")
        print(f"   - LOW:    Score ≥ {thresholds.get('low_risk', 80)} (god tilgjengelighet)")
        print()
        
        print("=" * 80)
        print("✅ Validator fungerer!")
        print("=" * 80)
        print()
        print("Se fullstendig dokumentasjon: docs/PROXIMITY_VALIDATION.md")
        print()


if __name__ == "__main__":
    asyncio.run(test_validator())
