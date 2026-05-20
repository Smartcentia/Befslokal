import asyncio
import sys
import os
import re

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select, or_, and_
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.models.text_content import TextContent
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def find_parking_in_text():
    async with SessionLocal() as db:
        print("Searching document text for parking information...\n")
        
        keywords = ["parkering", "garasje", "lading", "p-plass", "ladestasjon", "elbil", "biloppstilling"]
        
        # We search TextContent. 
        # Ideally linked to Contract or Property.
        # Fallback: Search all text content and try to infer location from metadata if direct link missing.
        

        # 1. Search text content linked to Contracts
        # Try finding ANY text content with keywords first
        stmt = select(TextContent)
        conditions = [TextContent.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = stmt.where(or_(*conditions))
        stmt = stmt.limit(100) # Safety limit
        
        result = await db.execute(stmt)
        rows = result.scalars().all()
        
        print(f"Found {len(rows)} text matches in TOTAL (unfiltered).\n")
        
        results_map = {} 

        for text_node in rows:
            content = text_node.content
            if not content:
                continue
                
            # Find context for each keyword
            matches = []
            content_lower = content.lower()
            
            for kw in keywords:
                for m in re.finditer(kw, content_lower):
                    start = max(0, m.start() - 100)
                    end = min(len(content), m.end() + 100)
                    context = content[start:end].replace("\n", " ").strip()
                    context = re.sub(r'\s+', ' ', context)
                    matches.append(f"...{context}...")
            
            if matches:
                 unique_matches = list(set(matches))
                 relevant_text = "\n".join(unique_matches[:3])
                 
                 # Try to resolve property/address from metadata or TextContent relationships
                 # This is a bit hacker-ish but necessary if relations are broken
                 address = "Unknown"
                 city = "Unknown"
                 
                 # Try DB links first
                 if text_node.contract_id:
                     contract = await db.get(Contract, text_node.contract_id)
                     if contract and contract.unit_id:
                         unit = await db.get(Unit, contract.unit_id)
                         if unit and unit.property_id:
                             prop = await db.get(Property, unit.property_id)
                             if prop:
                                 address = prop.address
                                 city = prop.city
                
                 # If still unknown, check if we can parse filename
                 source_file = text_node.source_file or text_node.source_index_id or "Unknown"
                 if address == "Unknown" and "/" in str(source_file):
                      # Guess address from filename like "contracts/Storgata 12/..."
                      parts = str(source_file).split("/")
                      if len(parts) > 1:
                          address = parts[-2] # Convention check

                 results_map[str(text_node.text_id)] = {
                     "address": address,
                     "city": city,
                     "text": relevant_text,
                     "source_file": source_file
                 }


        # Print Table
        print("| Address | City | Extracted Parking Info | Source File |")
        print("|---|---|---|---|")
        
        for cid, data in results_map.items():
            # Escape pipes in text
            safe_text = data['text'].replace("|", "/")
            print(f"| {data['address']} | {data['city']} | {safe_text} | {data['source_file']} |")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(find_parking_in_text())
