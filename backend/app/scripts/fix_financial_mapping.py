
import asyncio
import sys
import os
import json
import logging
from typing import List, Optional, Tuple
import re
from difflib import SequenceMatcher

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add backend to path
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file))) # .../backend
project_root = os.path.dirname(backend_dir) # .../KNOWME

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_database_url():
    env_path = os.path.join(os.getcwd(), 'backend', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

# Ensure DB URL is set for session
db_url = get_database_url()
if db_url:
    os.environ["DATABASE_URL"] = db_url

try:
    from app.domains.core.models.user import User
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.property import Property
    from app.db.session import SessionLocal
    from sqlalchemy import select, or_, func
except ImportError as e:
    logger.error(f"Import Error: {e}")
    # Fallback for script context
    from backend.app.domains.core.models.user import User
    from backend.app.domains.hms.models.risk import RiskAssessment
    from backend.app.domains.hms.models.internal_control import InternalControlCase
    from backend.app.domains.core.models.property import Property
    from backend.app.db.session import SessionLocal

def normalize_address(addr: str) -> str:
    """
    Normalize address for matching.
    - Lowercase
    - Remove punctuation
    - Remove zip codes (4 digits)
    - Standardize common variations
    """
    if not addr: 
        return ""
    
    # Lowercase
    norm = addr.lower().strip()
    
    # Remove comma
    norm = norm.replace(',', '')
    
    # Remove common words that might differ
    norm = norm.replace('gate', 'gt').replace('gata', 'gt').replace('veien', 'vn').replace('vei', 'vn')
    
    # Remove zip codes (4 digits) usually at end or middle
    # Strategy: remove any 4-digit sequence, unless it matches street number (unlikely to be exactly 4 digits without context, but risky)
    # Safer: Split by space, look for 4 digit token, remove it if it looks like a zip (leads city)
    
    parts = norm.split()
    cleaned_parts = []
    
    for p in parts:
        if p.isdigit() and len(p) == 4:
            continue # Skip zip-like numbers
        
        # Also remove city names if we can? 
        # Hard to know without a list. 
        # But if we compare street address vs street address we should be ok.
        
        cleaned_parts.append(p)
        
    return " ".join(cleaned_parts).strip()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

async def fix_financial_mapping(dry_run=True, promote_orphans=False):
    logger.info(f"Starting Robust Financial Mapping Fix (Dry Run: {dry_run}, Promote Orphans: {promote_orphans})")
    
    async with SessionLocal() as db:
        # Fetch all properties
        result = await db.execute(select(Property))
        all_props = result.scalars().all()
        
        # Categorize
        financial_props = [] # Sources
        candidate_masters = [] # Targets
        
        for p in all_props:
            ext = p.external_data or {}
            # Check if this property HAS financial data
            if 'financials' in ext:
                financial_props.append(p)
            else:
                # Potential master
                candidate_masters.append(p)
                
        logger.info(f"Sources (Financial Data): {len(financial_props)}")
        logger.info(f"Candidates (Master Props): {len(candidate_masters)}")
        
        linked_count = 0
        
        for p in financial_props:
            ext = p.external_data
            fin = ext.get('financials', {})
            
            # Extract Address from Dim 2 
            dim2_t = ext.get("Dim 2(T)") 
            if not dim2_t and isinstance(fin, dict):
                 dim2_t = fin.get('dim_2_original')
            if not dim2_t:
                 dim2_t = ext.get("Dim 2")

            if not dim2_t:
                logger.warning(f"Property {p.property_id} has financials but no address source.")
                continue

            # Clean/Normalize Source Address
            # Often looks like: "Tærudgata 16, 2004 Lillestrøm"
            # We want to match against "Tærudgata 16"
            
            # Pre-cleaning: simple split by comma to get street part
            street_part = dim2_t.split(',')[0]
            norm_source = normalize_address(street_part)
            
            best_match = None
            best_score = 0.0
            
            # Find best match in candidates
            for candidate in candidate_masters:
                # Don't match self (should be impossible due to filtering but safety first)
                if candidate.property_id == p.property_id:
                    continue
                    
                norm_cand = normalize_address(candidate.address or "")
                
                # Check 1: Exact Normalized Match
                if norm_source == norm_cand and norm_source:
                    best_match = candidate
                    best_score = 1.0
                    break
                
                # Check 2: Fuzzy Match
                score = similarity(norm_source, norm_cand)
                if score > best_score:
                    best_score = score
                    best_match = candidate
            
            # Threshold
            THRESHOLD = 0.85
            if best_match and best_score >= THRESHOLD:
                logger.info(f"MATCH: '{dim2_t}' (Norm: {norm_source}) matches '{best_match.address}' (Norm: {normalize_address(best_match.address or '')}) | Score: {best_score:.2f}")
                
                if not dry_run:
                    # Merge Logic
                    master = best_match
                    # Logic: 
                    # 1. Merge P's financial data into Match's external_data
                    match_ext = dict(master.external_data or {})
                    match_ext['financials'] = ext['financials'] # Use 'ext' from the source property 'p'
                    master.external_data = match_ext
                    
                    # 2. Rename P to indicate it's merged/obsolete or delete it?
                    # Strategy: Mark as "Merged into {match.id}" in notes or name
                    p.name = f"MERGED -> {master.name}"
                    p.is_active = False # Archive it
                    
                    db.add(master)
                    db.add(p)
                    linked_count += 1
            else:
                logger.warning(f"NO MATCH: '{dim2_t}' (Norm: {norm_source}). Best candidate: '{best_match.address if best_match else 'None'}' ({best_score:.2f})")
                
                # Promotion Logic
                if promote_orphans:
                    logger.info(f"  -> PROMOTING ORPHAN: {p.property_id}")
                    if not dry_run:
                        # Hydrate the orphan into a Master
                        # Use the Dim 2 T value as the official address and name
                        new_addr = dim2_t.split(",")[0].strip() # Simple cleanup "Storgata 1, 0101 Oslo" -> "Storgata 1"
                        p.address = new_addr
                        p.name = new_addr # Often property name is address
                        p.is_active = True
                        
                        # Remove 'financials' from external_data?? No, keep it, but maybe verify script won't loop?
                        # Actually, keeping it makes it a "financial prop" still. 
                        # Ideally we want it to BE a master. Masters defined as NOT having 'financials'?
                        # No, script defines masters as "all_props" at start.
                        
                        db.add(p)
                        linked_count += 1
                        logger.info(f"  -> Promoted to Master: {new_addr}")

        if dry_run:
            logger.info("Dry run complete. No changes made.")
        else:
            await db.commit()
            logger.info(f"Committed {linked_count} changes.")
            
        logger.info(f"Summary: Processed {linked_count} records.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true", help="Commit changes to DB")
    parser.add_argument("--promote-orphans", action="store_true", help="Promote unlinked properties to Masters")
    args = parser.parse_args()
    
    asyncio.run(fix_financial_mapping(dry_run=not args.commit, promote_orphans=args.promote_orphans))
