import asyncio
import json
import sys
import os
from difflib import SequenceMatcher
import asyncpg

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def similarity(a, b):
    """Calculate similarity ratio between two strings"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

async def main():
    # Load Bufdir data
    with open("bufdir_institutions.json", "r") as f:
        institutions = json.load(f)
    
    print(f"Loaded {len(institutions)} institutions from Bufdir")
    
    # Connect to database
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Load properties from database
        properties = await conn.fetch("""
            SELECT property_id, name, address, city, postal_code
            FROM properties
        """)
        
        print(f"Found {len(properties)} properties in database")
        
        matches = []
        unmatched_institutions = []
        
        for inst in institutions:
            inst_name = inst.get("name", "")
            inst_location = inst.get("location", "")
            
            best_match = None
            best_score = 0
            
            for prop in properties:
                prop_name = prop["name"] or ""
                prop_address = prop["address"] or ""
                prop_city = prop["city"] or ""
                
                # Calculate similarity scores
                name_score = similarity(inst_name, prop_name)
                location_score = 0
                
                if inst_location:
                    # Check if location matches city or address
                    if prop_city:
                        location_score = max(location_score, similarity(inst_location, prop_city))
                    if prop_address:
                        location_score = max(location_score, similarity(inst_location, prop_address))
                
                # Combined score (weighted)
                combined_score = (name_score * 0.7) + (location_score * 0.3)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = prop
            
            # Threshold for matching
            if best_score > 0.6:
                matches.append({
                    "institution": inst,
                    "property": {
                        "id": str(best_match["property_id"]),
                        "name": best_match["name"],
                        "address": best_match["address"],
                        "city": best_match["city"]
                    },
                    "score": best_score
                })
                print(f"✓ Matched: {inst_name} -> {best_match['name']} (score: {best_score:.2f})")
            else:
                unmatched_institutions.append(inst)
                print(f"✗ No match: {inst_name} (best score: {best_score:.2f})")
        
        # Save results
        with open("bufdir_matches.json", "w") as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
        
        with open("bufdir_unmatched.json", "w") as f:
            json.dump(unmatched_institutions, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== Summary ===")
        print(f"Matched: {len(matches)}")
        print(f"Unmatched: {len(unmatched_institutions)}")
        print(f"\nResults saved to bufdir_matches.json and bufdir_unmatched.json")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
