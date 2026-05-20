"""Service for importing Bufdir institutions into the database."""
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.crisis_center import CrisisCenter
# No self-import needed


logger = logging.getLogger(__name__)

async def import_bufdir_institutions(db: AsyncSession, json_file_path: str) -> dict:
    """
    Import institutions from Bufdir JSON file into the database.
    
    Args:
        db: Database session
        json_file_path: Path to institutions.json file
        
    Returns:
        Dictionary with import statistics
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        institutions = json.load(f)
    
    added = 0
    updated = 0
    skipped = 0
    
    for inst in institutions:
        # Check if center already exists by name
        result = await db.execute(
            select(CrisisCenter).where(CrisisCenter.name == inst['name'])
        )
        existing_center = result.scalar_one_or_none()
        
        if existing_center:
            # Update existing
            existing_center.location = inst.get('location')
            existing_center.url = inst.get('url')
            updated += 1
        else:
            # Create new
            new_center = CrisisCenter(
                name=inst['name'],
                location=inst.get('location'),
                url=inst.get('url')
            )
            db.add(new_center)
            added += 1
    
    await db.commit()
    
    logger.info(f"Import complete: {added} added, {updated} updated, {skipped} skipped")
    
    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "total": len(institutions)
    }
