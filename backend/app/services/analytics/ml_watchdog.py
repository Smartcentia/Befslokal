import logging
import asyncio
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.core.models.property import Property
from app.domains.hms.models.internal_control import Notification
from app.domains.core.models.user import User, UserRole
from app.services.analytics.financial_analytics import financial_analytics_service
from app.services.agent_memory_service import AgentMemoryService
import json

logger = logging.getLogger(__name__)

class MLWatchdog:
    """
    Background service that runs ML analysis on the entire portfolio
    to detect anomalies and update pattern memory.
    """

    @staticmethod
    async def scan_for_anomalies(db: AsyncSession):
        """
        Scan all properties for financial anomalies and create notifications for admins.
        """
        logger.info("🕵️ ML Watchdog: Starting global anomaly scan...")
        
        # 1. Get all properties
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # 2. Get all admin users for notifications
        stmt_admins = select(User).where(User.role == UserRole.ADMIN)
        result_admins = await db.execute(stmt_admins)
        admins = result_admins.scalars().all()
        
        anomaly_count = 0
        
        for prop in properties:
            # Detect anomalies using the financial_analytics_service
            analysis = await financial_analytics_service.detect_spending_anomalies(db, prop.property_id)
            
            if analysis and analysis.get("anomalies"):
                for anomaly in analysis["anomalies"]:
                    # Create notification for each admin
                    for admin in admins:
                        # Check if notification already exists to avoid spamming
                        # (simplistic check for this POC)
                        
                        notif = Notification(
                            user_id=admin.user_id,
                            title=f"Økonomisk avvik funnet: {prop.name}",
                            message=f"ML-gjenkjenning har funnet et unormalt kostnadsmønster i år {anomaly['year']}: {anomaly['amount']:,.0f} kr ({anomaly['reason']}).",
                            notification_type="ml_anomaly",
                            related_entity_type="property",
                            related_entity_id=prop.property_id
                        )
                        db.add(notif)
                    anomaly_count += 1
        
        await db.commit()
        logger.info(f"🕵️ ML Watchdog: Scan complete. Found {anomaly_count} potential anomalies.")
        return anomaly_count

    @staticmethod
    async def update_pattern_memory(db: AsyncSession):
        """
        Updates the long-term memory of the AI with the latest portfolio-wide patterns.
        """
        try:
            logger.info("🕵️ ML Watchdog: Updating global pattern memory...")
            
            from app.services.analytics.financial_analysis_service import FinancialAnalysisService
            patterns = await FinancialAnalysisService.get_common_patterns(db)
            
            # Store in Agent Memory so KI Kollega can "remember" it without recalculating
            memory_content = f"SISTE PORTESØLJE-ANALYSE ({json.dumps(patterns.get('total_properties'))} eiendommer):\n"
            memory_content += f"- Vanligste kategorier: {', '.join([c['category'] for c in patterns.get('common_categories', [])[:3]])}\n"
            
            if patterns.get("cluster_patterns"):
                 memory_content += f"- Klyngestruktur: {len(patterns['cluster_patterns'].get('clusters', []))} aktive kostnadsgrupper identifisert.\n"

            await AgentMemoryService.add_memory(
                db, 
                content=memory_content, 
                metadata={
                    "type": "portfolio_patterns",
                    "timestamp": str(asyncio.get_event_loop().time()),
                    "source": "ml_watchdog"
                }
            )
            logger.info("🕵️ ML Watchdog: Pattern memory updated.")
        except Exception as e:
            logger.warning(f"⚠️ ML Watchdog: Could not update pattern memory: {e}")

async def run_watchdog():
    from app.db.session import SessionLocal
    # Import base to load all models for SQLAlchemy registry
    import app.db.base
    async with SessionLocal() as db:
        watchdog = MLWatchdog()
        await watchdog.scan_for_anomalies(db)
        await watchdog.update_pattern_memory(db)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_watchdog())
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_watchdog())
