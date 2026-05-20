
import asyncio
import sys
import os
import re
from sqlalchemy import select
from difflib import get_close_matches

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Models for registry
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

INPUT_FILE = "backend/docs/noe.txt"

async def map_ids():
    # 1. Load DB Properties
    async with SessionLocal() as session:
        result = await session.execute(select(Property))
        properties = result.scalars().all()
        db_names = {str(p.property_id): p.name for p in properties}
        print(f"Loaded {len(db_names)} DB properties.")

    # 2. Extract IDs from noe.txt
    noe_map = {} # ID -> set(Names)
    result_map = {} # ID -> Best Name
    
    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        match = re.search(r'^(.*?) (\d{6}) (.*) ((-?[\d]+,[\d]+)|(-?[\d]+))$', line)
        if match:
            pid = match.group(2)
            # Middle includes property name + category
            middle = match.group(3)
            # Heuristic: Prop name is start of middle.
            # We don't need perfect split, just fuzzy source.
            if pid not in noe_map: noe_map[pid] = []
            noe_map[pid].append(middle)
            
    print(f"Found {len(noe_map)} unique IDs in noe.txt")
    
    # Consolidate Names
    # Middle starts with Property Name.
    # We can take the longest common prefix? Or just the most frequent middle start?
    # Simple: Just take the first one found, cutoff at "Category" if possible.
    
    categories = [
        "Barnevernsinstitusjoner", "Fosterhjemstjenesten", "Regionale fellesfunksjoner",
        "Sentre for foreldre og barn", "Familieverntjeneste", "Omsorgssentre for mindreårige",
        "Statlig regionalt barnevernmyndighet", "Beredskapshjem", "Inntak", "Fosterhjem", "Hjelpetiltak i hjemmet"
    ]
    
    final_id_name = {}
    
    for pid, middles in noe_map.items():
        # Clean middle
        sample = middles[0]
        prop_name = sample
        for cat in sorted(categories, key=len, reverse=True):
             if cat in sample:
                 prop_name = sample.split(cat)[0].strip()
                 break
        final_id_name[pid] = prop_name
        
    # Match
    print("\n--- Mapping Report ---")
    print(f"{'ID':<10} | {'NOE Name':<40} | {'DB Match':<40}")
    print("-" * 100)
    
    db_name_list = list(db_names.values())
    
    mapped_count = 0
    
    for pid, name in final_id_name.items():
        # 1. Exact match (case insensitive)
        match = None
        for dbn in db_name_list:
            if name.lower() == dbn.lower():
                match = dbn
                break
        
        # 2. Substring
        if not match:
            for dbn in db_name_list:
                if name.lower() in dbn.lower() or dbn.lower() in name.lower():
                    # Avoid short matches
                    if len(name) > 4 and len(dbn) > 4:
                        match = dbn
                        break
                        
        # 3. Fuzzy
        if not match:
            fuzzy = get_close_matches(name, db_name_list, n=1, cutoff=0.6)
            if fuzzy:
                match = f"{fuzzy[0]} (Fuzzy)"
                
        if match:
            mapped_count += 1
            
        print(f"{pid:<10} | {name[:40]:<40} | {match or 'NO MATCH'}")
        
    print(f"\nTotal Mapped: {mapped_count} / {len(final_id_name)}")

if __name__ == "__main__":
    asyncio.run(map_ids())
