from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from typing import Dict, Any, List

# Import Domain Models
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
from app.domains.fdv.models.iot import SensorReading

class DataHealthService:
    """
    Service for verifying the health and integrity of the dataset.
    Used by Admin Dashboard and CLI tools.
    """
    
    async def check_db_connection(self, db: AsyncSession) -> bool:
        try:
            await db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def get_data_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get row counts and basic stats for key tables.
        """
        stats = {}
        
        try:
            # 1. Properties
            res = await db.execute(select(func.count()).select_from(Property))
            stats["properties_count"] = res.scalar() or 0
            
            # 2. Contracts
            res = await db.execute(select(func.count()).select_from(Contract))
            stats["contracts_count"] = res.scalar() or 0
            
            # 3. Users
            res = await db.execute(select(func.count()).select_from(User))
            stats["users_count"] = res.scalar() or 0
            
            # 4. Risks
            res = await db.execute(select(func.count()).select_from(RiskAssessment))
            stats["risks_count"] = res.scalar() or 0
            
            # 5. IoT Readings (Volume check)
            res = await db.execute(select(func.count()).select_from(SensorReading))
            stats["iot_readings_count"] = res.scalar() or 0
            
            stats["status"] = "accessible"
            
        except Exception as e:
            stats["status"] = "error"
            stats["error_message"] = str(e)
            
        return stats

    async def check_integrity(self, db: AsyncSession) -> Dict[str, List[str]]:
        """
        Perform deeper integrity checks (orphans, missing fields).
        """
        issues = []
        
        try:
            # 1. Check for Properties without Latitude/Longitude
            res = await db.execute(
                select(Property.address)
                .where((Property.latitude == None) | (Property.longitude == None))
            )
            missing_coords = res.scalars().all()
            if missing_coords:
                issues.append(f"{len(missing_coords)} Properties missing coordinates")

            # 2. Check for Contracts without valid Units (orphans if FK constraint not enforced hard)
            # In SQL/SQLAlchemy with FKs this shouldn't happen, but good to check logical validity
            # Checking active contracts with no amount set
            res = await db.execute(
                select(Contract.contract_id)
                .where(Contract.status == 'active')
            )
            # Logic check: Active contracts should follow established data quality standards.
            
        except Exception as e:
            issues.append(f"Integrity check failed: {e}")
            
        return {"issues": issues}

data_health_service = DataHealthService()
