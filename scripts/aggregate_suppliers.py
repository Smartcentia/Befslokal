
import os
import re
import json
import csv
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/befs")

async def aggregate_supplier_info():
    suppliers = {}

    def add_supplier(name, category):
        if not name: return
        name = name.strip()
        if not name: return
        
        # Clean name a bit (remove trailing IDs or parentheses if they look like internal codes)
        # But be careful not to remove "AS" or "ASA"
        if name not in suppliers:
            suppliers[name] = set()
        if category:
            suppliers[name].add(category.strip())

    # 1. Process local documentation files
    docs_dir = "/Users/frank/Documents/BEFS_CLEAN/backend/docs"
    txt_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')]
    
    print(f"Processing {len(txt_files)} text files in docs...")
    for filename in txt_files:
        filepath = os.path.join(docs_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Try to find sequences that look like: Category Vendor Amount
                    # The format seems to be: ... Category Vendor Amount
                    # We'll use a regex or just split. 
                    # From what I saw: ... [Category] [Vendor] [Amount]
                    # Example: "Barnevernsinstitusjoner Reparasjon og vedlikehold leide lokaler Mjøsdata AS (64010635053) 16236,88"
                    # Category is usually several words.
                    
                    # Heuristic: split by common categories
                    categories = [
                        "Reparasjon og vedlikehold leide lokaler",
                        "Renhold lokaler",
                        "Renovasjon, vann, avløp o.l.",
                        "Strøm og oppvarming",
                        "Annen kostnad lokaler",
                        "Vakthold lokaler",
                        "Vaktmestertjenester",
                        "Leie parkeringsplass",
                        "Fellesutgifter andre utleiere",
                        "Leie lokaler andre utleiere"
                    ]
                    
                    for cat in categories:
                        if cat in line:
                            # Vendor is usually what's after the category and before the amount
                            parts = line.split(cat)
                            if len(parts) > 1:
                                after_cat = parts[1].strip()
                                # Amount is usually at the end, often with comma
                                # Look for the last number
                                match = re.search(r'([\w\s.&/-]+?)\s+(-?\d+,?\d*|-?\d+\.?\d*)$', after_cat)
                                if match:
                                    vendor = match.group(1).strip()
                                    add_supplier(vendor, cat)
                                elif "  " in after_cat: # Fallback
                                    vendor = after_cat.split("  ")[0].strip()
                                    add_supplier(vendor, cat)
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # 2. Process Database
    print("Connecting to database...")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Properties manual_expenses
        print("Extracting from properties table...")
        res = await session.execute(text("SELECT external_data FROM properties WHERE external_data IS NOT NULL"))
        rows = res.fetchall()
        for row in rows:
            ext_data = row[0]
            if not ext_data: continue
            expenses = ext_data.get('financials', {}).get('manual_expenses', [])
            for exp in expenses:
                add_supplier(exp.get('provider'), exp.get('type'))

        # Parties table
        print("Extracting from parties table...")
        try:
            res = await session.execute(text("SELECT name, external_data FROM parties"))
            rows = res.fetchall()
            for row in rows:
                name = row[0]
                ext_data = row[1]
                category = "General Provider"
                if ext_data and 'services' in ext_data:
                    if isinstance(ext_data['services'], list):
                        for s in ext_data['services']:
                            add_supplier(name, s)
                    else:
                        add_supplier(name, ext_data['services'])
                else:
                    add_supplier(name, category)
        except Exception as e:
            print(f"Parties table error: {e}")

    # Final Output preparation
    results = []
    for name, cats in suppliers.items():
        results.append({
            "Leverandør": name,
            "Tjenester": ", ".join(sorted(list(cats)))
        })

    # Sort results
    results.sort(key=lambda x: x["Leverandør"])

    # Save to CSV
    csv_path = 'leverandoroversikt_komplett.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Leverandør", "Tjenester"])
        writer.writeheader()
        writer.writerows(results)

    # Also save a markdown summary for the user
    md_path = 'LEVERANDORSAMMENSTILLING.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Komplett Leverandøroversikt\n\n")
        f.write(f"Totalt antall unike leverandører identifisert: {len(results)}\n\n")
        f.write("| Leverandør | Tjenester / Artikler |\n")
        f.write("| :--- | :--- |\n")
        # Write first 100 as a sample in the MD, link to CSV for rest
        for item in results[:100]:
            f.write(f"| {item['Leverandør']} | {item['Tjenester']} |\n")
        f.write("\n... og mange flere. Se komplett oversikt i [leverandoroversikt_komplett.csv](leverandoroversikt_komplett.csv).\n")

    print(f"Aggregation complete. Found {len(results)} suppliers.")
    print(f"Results saved to {csv_path} and {md_path}")

if __name__ == "__main__":
    asyncio.run(aggregate_supplier_info())
