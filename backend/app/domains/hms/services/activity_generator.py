"""
Activity Generator Service
Automatically generates scheduled activities based on property metadata tags.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
import logging

from app.domains.core.models.property import Property
from app.domains.core.models.user import User, UserRole
from app.domains.hms.models.scheduled_activity import ScheduledActivity, ActivityTemplate

logger = logging.getLogger(__name__)


class ActivityGenerator:
    """
    Generates scheduled activities based on property characteristics.
    Uses predefined templates and property metadata to create recurring tasks.
    """
    
    # Default activity templates based on HMS documentation
    DEFAULT_TEMPLATES = [
        # Institution-specific (RKL6)
        {
            "title": "Sjekk brannsentral",
            "description": "Daglig visuell kontroll av brannsentral for feil og alarmer",
            "category": "brann",
            "priority": "high",
            "activity_type": "daily",
            "recurrence_pattern": {"frequency": "daily", "interval": 1},
            "responsible_role": "vaktmester",
            "property_tags_required": ["Institusjon"],
        },
        {
            "title": "Sjekk rømningsveier",
            "description": "Kontroller at alle rømningsveier er frie for hindringer",
            "category": "brann",
            "priority": "critical",
            "activity_type": "daily",
            "recurrence_pattern": {"frequency": "daily", "interval": 1},
            "responsible_role": "vaktmester",
            "property_tags_required": ["Institusjon"],
        },
        {
            "title": "Test nødåpner på dører",
            "description": "Test at alle dører med nødåpnere åpnes automatisk ved brannalarm",
            "category": "sikkerhet",
            "priority": "critical",
            "activity_type": "monthly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 1},
            "responsible_role": "vaktmester",
            "property_tags_required": ["RKL6"],
        },
        {
            "title": "Kontroll av sikkerhetsglass",
            "description": "Inspeksjon av vinduer og glassfelt for skader",
            "category": "sikkerhet",
            "priority": "high",
            "activity_type": "quarterly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 15},
            "responsible_role": "eiendomsansvarlig",
            "property_tags_required": ["Institusjon"],
        },
        # Ventilation and indoor climate
        {
            "title": "Ventilasjonskontroll",
            "description": "Sjekk ventiler i fellesarealer, rengjør synlige ventiler",
            "category": "inneklima",
            "priority": "medium",
            "activity_type": "weekly",
            "recurrence_pattern": {"frequency": "weekly", "interval": 1, "day_of_week": 1},  # Monday
            "responsible_role": "vaktmester",
            "property_tags_required": None,  # All properties
        },
        # Fire safety equipment
        {
            "title": "Kontroll av håndslukkere",
            "description": "Månedlig egenkontroll: tilstedeværelse, trykk, plombering",
            "category": "brann",
            "priority": "high",
            "activity_type": "monthly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 5},
            "responsible_role": "vaktmester",
            "property_tags_required": None,
        },
        {
            "title": "Kontroll av nødlys",
            "description": "Visuell sjekk at alle nødlysarmaturer lyser (grønn LED)",
            "category": "brann",
            "priority": "medium",
            "activity_type": "monthly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 10},
            "responsible_role": "vaktmester",
            "property_tags_required": None,
        },
        # Leased property - landlord interface
        {
            "title": "Temperatur- og luftkvalitetslogging",
            "description": "Dokumenter inneklima for grensesnitt mot utleier (morgen, lunsj, ettermiddag)",
            "category": "inneklima",
            "priority": "medium",
            "activity_type": "monthly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 20},
            "responsible_role": "eiendomsansvarlig",
            "property_tags_required": ["Leid"],
        },
        {
            "title": "Grensesnittmøte med utleier",
            "description": "Gjennomgang av avvik og vedlikeholdsstatus med gårdeier",
            "category": "hms",
            "priority": "medium",
            "activity_type": "quarterly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 1},
            "responsible_role": "områdeleder",
            "property_tags_required": ["Leid"],
        },
        # Annual compliance
        {
            "title": "Brannøvelse",
            "description": "Gjennomføring av årlig brannøvelse for alle ansatte og beboere",
            "category": "brann",
            "priority": "critical",
            "activity_type": "annual",
            "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 3, "day_of_month": 15},  # March 15
            "responsible_role": "områdeleder",
            "property_tags_required": None,
        },
        {
            "title": "ROS-analyse gjennomgang",
            "description": "Årlig gjennomgang og oppdatering av risiko- og sårbarhetsanalyse",
            "category": "hms",
            "priority": "high",
            "activity_type": "annual",
            "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 1, "day_of_month": 31},  # January 31
            "responsible_role": "områdeleder",
            "property_tags_required": None,
        },
        # Office-specific
        {
            "title": "HMS-runde: Ergonomi og belysning",
            "description": "Kontroll av arbeidsplasser for ergonomi og belysningskvalitet",
            "category": "hms",
            "priority": "medium",
            "activity_type": "monthly",
            "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 25},
            "responsible_role": "eiendomsansvarlig",
            "property_tags_required": ["Kontor"],
        },
    ]

    @staticmethod
    def calculate_next_due_date(recurrence: Dict[str, Any], from_date: Optional[datetime] = None) -> datetime:
        """
        Calculate next due date based on recurrence pattern.
        """
        from datetime import timezone
        base_date = from_date or datetime.now(timezone.utc)
        frequency = recurrence.get("frequency", "monthly")
        interval = recurrence.get("interval", 1)

        if frequency == "daily":
            return base_date + timedelta(days=interval)
        
        elif frequency == "weekly":
            day_of_week = recurrence.get("day_of_week", 1)  # Monday = 1
            days_ahead = day_of_week - base_date.isoweekday()
            if days_ahead <= 0:
                days_ahead += 7 * interval
            return base_date + timedelta(days=days_ahead)
        
        elif frequency == "monthly":
            day_of_month = recurrence.get("day_of_month", 1)
            # Simple implementation: add months and set day
            target_month = base_date.month + interval
            target_year = base_date.year
            while target_month > 12:
                target_month -= 12
                target_year += 1
            
            try:
                return datetime(target_year, target_month, day_of_month, tzinfo=base_date.tzinfo)
            except ValueError:
                # Handle invalid dates (e.g., Feb 30)
                return datetime(target_year, target_month, 28, tzinfo=base_date.tzinfo)
        
        elif frequency == "yearly":
            month = recurrence.get("month", 1)
            day_of_month = recurrence.get("day_of_month", 1)
            target_year = base_date.year + interval
            
            try:
                return datetime(target_year, month, day_of_month, tzinfo=base_date.tzinfo)
            except ValueError:
                return datetime(target_year, month, 28, tzinfo=base_date.tzinfo)
        
        else:
            # Default fallback
            return base_date + timedelta(days=30 * interval)

    @staticmethod
    def property_matches_tags(property_tags: List[str], required: Optional[List[str]], excluded: Optional[List[str]]) -> bool:
        """
        Check if property tags match the template requirements.
        """
        if not property_tags:
            property_tags = []
        
        # Check required tags (ALL must be present)
        if required:
            if not all(tag in property_tags for tag in required):
                return False
        
        # Check excluded tags (NONE can be present)
        if excluded:
            if any(tag in property_tags for tag in excluded):
                return False
        
        return True

    async def generate_activities_for_property(
        self, 
        db: AsyncSession, 
        property_id: UUID,
        templates: Optional[List[Dict[str, Any]]] = None
    ) -> List[ScheduledActivity]:
        """
        Generate scheduled activities for a specific property based on templates.
        """
        # Get property with metadata
        result = await db.execute(
            select(Property).where(Property.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            logger.warning(f"Property {property_id} not found")
            return []
        
        # Extract property tags from external_data
        external_data = property_obj.external_data or {}
        if isinstance(external_data, str):
            import json
            try:
                external_data = json.loads(external_data)
            except Exception:
                external_data = {}
        property_tags = external_data.get("tags", [])
        
        if templates is None:
            templates = self.DEFAULT_TEMPLATES
        
        generated_activities = []
        
        for template in templates:
            # Check if template matches property tags
            if not self.property_matches_tags(
                property_tags,
                template.get("property_tags_required"),
                template.get("property_tags_excluded")
            ):
                continue
            
            # Check if activity already exists
            existing = await db.execute(
                select(ScheduledActivity).where(
                    and_(
                        ScheduledActivity.property_id == property_id,
                        ScheduledActivity.title == template["title"],
                        ScheduledActivity.enabled == True
                    )
                )
            )
            if existing.scalars().first():
                logger.debug(f"Activity '{template['title']}' already exists for property {property_id}")
                continue
            
            # Calculate first due date
            next_due = self.calculate_next_due_date(template["recurrence_pattern"])
            
            # Create activity
            activity = ScheduledActivity(
                property_id=property_id,
                title=template["title"],
                description=template.get("description"),
                activity_type=template["activity_type"],
                category=template["category"],
                priority=template["priority"],
                responsible_role=template["responsible_role"],
                recurrence_rule=template["recurrence_pattern"],
                next_due_date=next_due,
                property_tags_required=template.get("property_tags_required"),
                property_tags_excluded=template.get("property_tags_excluded"),
                enabled=True,
                created_by="system"
            )
            
            db.add(activity)
            generated_activities.append(activity)
            logger.info(f"Generated activity '{template['title']}' for property {property_id}, next due: {next_due}")
        
        await db.commit()
        return generated_activities

    async def generate_activities_for_all_properties(self, db: AsyncSession) -> Dict[str, int]:
        """
        Generate activities for all properties in the system.
        Returns statistics about generation.
        """
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        stats = {
            "total_properties": len(properties),
            "total_activities_generated": 0,
            "properties_with_activities": 0
        }
        
        for prop in properties:
            activities = await self.generate_activities_for_property(db, prop.property_id)
            if activities:
                stats["total_activities_generated"] += len(activities)
                stats["properties_with_activities"] += 1
        
        logger.info(f"Activity generation complete: {stats}")
        return stats
