import asyncio
import sys
import os
import re
import json

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select, or_
from sqlalchemy.orm.attributes import flag_modified
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

async def analyze_costs(client, text, address):
    if not client:
        return {"summary": "LLM Error", "common_costs": "Unknown", "electricity": "Unknown", "heating": "Unknown"}

    prompt = f"""
    Analyze the following text regarding costs (felleskostnader, strøm, energi) for the property at {address}.
    
    Extract who pays for what, or if it is included in the rent.
    Focus on:
    - Common Costs (Felleskostnader): Included, Separate (Akonto), or Tenant Direct?
    - Electricity (Strøm): Included, Separate Sub-meter (Undermåler), or Tenant subscription?
    - Heating (Varme/Fjernvarme): Included, Separate, or Tenant?

    Text Snippet:
    "{text}"

    JSON Output Format:
    {{
        "summary": "1-sentence summary of the cost structure.",
        "common_costs": "Inkludert" | "Akonto" | "Direkte" | "Ukjent",
        "electricity": "Inkludert" | "Leietaker (Eget)" | "Leietaker (Undermåler)" | "Utleier" | "Ukjent",
        "heating": "Inkludert" | "Leietaker" | "Akonto" | "Ukjent",
        "specific_costs": ["List strings like 'Brøyting: 50%', 'Heis: Ink'"]
    }}
    """
    
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a real estate cost analyst. Output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"summary": "Error", "error": str(e)}

async def run_extraction():
    client = await get_llm_client()
    if not client:
        print("Failed to initialize OpenAI client.")
        return

    async with SessionLocal() as db:
        print("Searching and analyzing cost drivers...\n")
        
        keywords = ["felleskostnader", "strøm", "varme", "fjernvarme", "nettleie", "avgifter", "vaktmester"]
        
        # 1. Broad Search
        stmt = select(TextContent)
        conditions = [TextContent.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = stmt.where(or_(*conditions)).limit(30)
        
        result = await db.execute(stmt)
        rows = result.scalars().all()
        
        results_map = {} 

        for text_node in rows:
            content = text_node.content
            if not content: continue

            matches = []
            content_lower = content.lower()
            for kw in keywords:
                for m in re.finditer(kw, content_lower):
                    start = max(0, m.start() - 200)
                    end = min(len(content), m.end() + 200)
                    matches.append(content[start:end].replace("\n", " ").strip())
            
            if matches:
                 relevant_text = "\n---\n".join(list(set(matches))[:3])
                 
                 # Resolve Address
                 address = "Unknown"
                 if text_node.contract_id:
                     contract = await db.get(Contract, text_node.contract_id)
                     if contract and contract.unit_id:
                         unit = await db.get(Unit, contract.unit_id)
                         if unit and unit.property_id:
                             prop = await db.get(Property, unit.property_id)
                             if prop: address = prop.address

                 contract_id = str(text_node.contract_id) if text_node.contract_id else None
                 
                 if address == "Unknown":
                      src = str(text_node.source_file or text_node.source_index_id or "Unknown")
                      if "/" in src:
                          parts = src.split("/")
                          address = parts[-2] if len(parts) > 1 else src
                      else:
                          address = src.replace(".pdf", "").replace(".txt", "")

                 if address != "Unknown" and address not in results_map:
                     print(f"Analyzing costs for {address}...")
                     analysis = await analyze_costs(client, relevant_text, address)
                     if contract_id:
                         analysis["contract_id"] = contract_id
                     analysis["source_file"] = str(text_node.source_file or "N/A")
                     results_map[address] = analysis

        # Save to DB
        print(f"\nSaving {len(results_map)} insights to database...")
        for addr, data in results_map.items():
            stmt = select(Property).where(Property.address.ilike(f"%{addr}%")).limit(1)
            res = await db.execute(stmt)
            prop = res.scalar_one_or_none()
            
            if prop:
                current_data = prop.external_data or {}
                ai_insights = current_data.get("ai_insights", {})
                
                ai_insights["costs"] = {
                    "found": True,
                    "summary": data.get("summary", ""),
                    "common_costs": data.get("common_costs", "Ukjent"),
                    "electricity": data.get("electricity", "Ukjent"),
                    "heating": data.get("heating", "Ukjent"),
                    "details": data.get("specific_costs", []),
                    "details": data.get("specific_costs", []),
                    "source_file": data.get("source_file", ""),
                    "source_contract_id": data.get("contract_id"),
                    "updated_at": "2026-01-02T15:25:00"
                }
                
                current_data["ai_insights"] = ai_insights
                prop.external_data = current_data
                flag_modified(prop, "external_data")
                db.add(prop)
                print(f"✅ Updated {prop.address}")
            else:
                print(f"⚠️ No property match for '{addr}'")
        
        await db.commit()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_extraction())
