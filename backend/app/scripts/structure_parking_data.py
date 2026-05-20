import asyncio
import sys
import os
import re
import json

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select, or_
from app.db.session import SessionLocal
from app.models.text_content import TextContent
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User
from app.core.config import settings
from openai import AsyncOpenAI

async def get_llm_client():
    if not settings.OPENAI_API_KEY:
        return None
        
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )

async def analyze_with_llm(client, text, address):
    if not client:
        return {"parking": "Unknown", "cost": "Unknown", "details": "LLM Client Failed"}

    prompt = f"""
    Analyze the following text regarding parking for the property at {address}.
    Extract the following information in JSON format:
    1. "coverage": Does the rent include parking? (Options: "Inkludert", "Separat leie", "Nei/Ikke nevnt", "Elbil-lading")
    2. "cost": Any costs mentioned? (Normalize to NOK/mnd if possible, or "Inkludert").
    3. "details": A brief 1-sentence summary of the parking situation (number of spots, garage vs outdoor, charging, etc).

    Text Snippet:
    "{text}"

    JSON Output Example:
    {{
        "coverage": "Inkludert",
        "cost": "0",
        "details": "6 garasjeplasser er inkludert i leien."
    }}
    """
    
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"coverage": "Error", "cost": "Error", "details": str(e)}

async def structure_parking_data():
    client = await get_llm_client()
    if not client:
        print("Failed to initialize OpenAI client. Check API key.")
        return

    async with SessionLocal() as db:
        print("Searching and analyzing parking data...\n")
        
        keywords = ["parkering", "garasje", "lading", "p-plass", "ladestasjon", "elbil"]
        
        stmt = select(TextContent)
        conditions = [TextContent.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = stmt.where(or_(*conditions))
        stmt = stmt.limit(20) # Limit for demo/speed purposes, increase for full scan
        
        result = await db.execute(stmt)
        rows = result.scalars().all()
        
        results_map = {} 

        for text_node in rows:
            content = text_node.content
            if not content:
                continue

            matches = []
            content_lower = content.lower()
            for kw in keywords:
                for m in re.finditer(kw, content_lower):
                    start = max(0, m.start() - 150)
                    end = min(len(content), m.end() + 150)
                    context = content[start:end].replace("\n", " ").strip()
                    context = re.sub(r'\s+', ' ', context)
                    matches.append(context)
            
            if matches:
                 unique_matches = list(set(matches))
                 relevant_text = "\n".join(unique_matches[:2])
                 
                 # Resolve Address
                 address = "Unknown"
                 if text_node.contract_id:
                     contract = await db.get(Contract, text_node.contract_id)
                     if contract and contract.unit_id:
                         unit = await db.get(Unit, contract.unit_id)
                         if unit and unit.property_id:
                             prop = await db.get(Property, unit.property_id)
                             if prop:
                                 address = prop.address

                 contract_id = str(text_node.contract_id) if text_node.contract_id else None
                

                 if address == "Unknown":
                      # Better fallback for source_file
                      src = str(text_node.source_file or text_node.source_index_id or "Unknown")
                      if "/" in src:
                          parts = src.split("/")
                          # heuristic: take the folder name if it looks like an address, else filename
                          if len(parts) > 1:
                              address = parts[-2]
                          else:
                              address = src
                      else:
                          # Flat filename
                          address = src.replace(".pdf", "").replace(".txt", "")

                 # Filter out duplicates by address if we already have a good one
                 if address != "Unknown" and address in results_map:
                     continue

                 # Call LLM
                 print(f"Analyzing {address}...")
                 analysis = await analyze_with_llm(client, relevant_text, address)
                 if contract_id:
                     analysis["contract_id"] = contract_id
                 analysis["source_file"] = str(text_node.source_file or "N/A")
                 
                 results_map[address] = analysis

        # Save to Database
        print("Saving insights to database...")
        for addr, data in results_map.items():
            # Try to match address to a real property
            # For simplicity in this script, we'll try an exact or fuzzy match strictly on address if we don't have ID
            # But earlier logic tried to get property object. Let's make sure we have property ID if possible.
            
            prop_id = None
            
            # Re-fetch property based on address string if we lost the ID map
            # Ideally we should have stored ID in results_map. Let's refactor slightly above to store (prop_id, address) as key or in value.
            # But given the current loop structure, let's do a best-effort lookup.
            
            # Using ILIKE for address match
            stmt = select(Property).where(Property.address.ilike(f"%{addr}%")).limit(1)
            res = await db.execute(stmt)
            prop = res.scalar_one_or_none()
            
            if prop:
                # Update external_data
                current_data = prop.external_data or {}
                # Ensure ai_insights dict exists
                ai_insights = current_data.get("ai_insights", {})
                
                ai_insights["parking"] = {
                    "found": True,
                    "summary": data.get("details", "Ingen detaljer"),
                    "cost": data.get("cost", "Ukjent"),
                    "coverage": data.get("coverage", "Ukjent"),
                    "coverage": data.get("coverage", "Ukjent"),
                    "source_file": data.get("source_file", "Ukjent kilde"),
                    "source_contract_id": data.get("contract_id"),
                    "updated_at": "2026-01-02T15:00:00" # ISO placeholder
                }
                
                current_data["ai_insights"] = ai_insights
                
                # SQLAlchemy requires flagging JSON mutation often, but standard assignment usually works if we re-assign the whole dict
                # prop.external_data = current_data # This might not trigger tracking if we mutate in place.
                # Safe way:
                from sqlalchemy.orm.attributes import flag_modified
                prop.external_data = current_data
                flag_modified(prop, "external_data")
                
                db.add(prop)
                print(f"✅ Updated {prop.address} with AI parking data.")
            else:
                print(f"⚠️ Could not find exact property match for '{addr}' in DB to save data.")
        
        await db.commit()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(structure_parking_data())
