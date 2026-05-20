
import logging
from app.db.session import SessionLocal
from app.services.creator.creator_agent import CreatorAgent

logger = logging.getLogger(__name__)

async def run_evolution_job():
    """
    Scheduled job to run the Creator Agent.
    """
    logger.info("🧬 Evolution Job: Starting...")
    
    agent = CreatorAgent()
    
    async with SessionLocal() as db:
        try:
            new_tools = await agent.analyze_and_create(db, limit=50)
            
            if new_tools:
                logger.info(f"🧬 Evolution Job: Created {len(new_tools)} new tools: {new_tools}")
            else:
                logger.info("🧬 Evolution Job: No new patterns found.")
                
        except Exception as e:
            logger.error(f"❌ Evolution Job Failed: {e}")
