import asyncio
import sys
import os
from sqlalchemy import select
from dotenv import load_dotenv
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

OUTPUT_FILE = "/Users/frank/.gemini/antigravity/brain/af321d5a-1361-49ed-a12f-6d185a662847/financial_inventory.md"

async def generate_report():
    print("Fetching properties...")
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        financial_props = []
        total_system_spend = 0.0
        
        for p in properties:
            ext = p.external_data or {}
            fin = ext.get('financials', {})
            
            # Check for ANY financial data
            total_manual = fin.get('total_manual_expenses', 0) or 0
            total_csv = fin.get('total_spend_csv', 0) or 0
            # Note: We zeroed total_spend_csv for manual entries, so sum should be correct
            total_spend = total_manual + total_csv
            
            manual_items = fin.get('manual_expenses', [])
            
            if total_spend > 0 or len(manual_items) > 0:
                financial_props.append({
                    "name": p.name,
                    "address": p.address,
                    "total": total_spend,
                    "items": len(manual_items),
                    "sources": ", ".join(set([x.get('source', 'unknown') for x in manual_items if isinstance(x, dict)])) or "legacy-csv"
                })
                total_system_spend += total_spend
                
        # Sort by Total Spend Descending
        financial_props.sort(key=lambda x: x['total'], reverse=True)
        
        # Generate Markdown
        md = "# Full Financial Data Inventory\n\n"
        md += f"**Total Properties with Financials:** {len(financial_props)}\n"
        md += f"**Total System Spend:** {total_system_spend:,.2f} NOK\n\n"
        
        md += "| Property Name | Address | Total Spend (NOK) | Items | Sources |\n"
        md += "| :--- | :--- | :--- | :--- | :--- |\n"
        
        for prop in financial_props:
            md += f"| {prop['name']} | {prop['address']} | {prop['total']:,.2f} | {prop['items']} | {prop['sources']} |\n"
            
        print(f"Found {len(financial_props)} properties. Writing to {OUTPUT_FILE}...")
        
        with open(OUTPUT_FILE, "w") as f:
            f.write(md)

if __name__ == "__main__":
    asyncio.run(generate_report())
