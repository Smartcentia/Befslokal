
import asyncio
import sys
import os
import re
from typing import List, Dict, Optional
from sqlalchemy import select
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
# Import ALL models to avoid mapper errors during check_configure
from app.domains.core.models.user import User
from app.models.file_meta import FileMeta
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

def similar(a, b):
    # Normalize by removing common suffixes
    a_clean = a.lower().replace("(løpende avtale)", "").replace("(utfaset)", "").strip()
    b_clean = b.lower().replace("(løpende avtale)", "").replace("(utfaset)", "").strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

STOP_TOKENS = {
    "Barnevernsinstitusjoner", "Regionale", "Fosterhjem", "Familievern", 
    "Inntak", "Ungdomssenter", "Omsorgssenter", "Direktoratet", "Administrasjon",
    "Fosterhjemstjenesten", "Strøm", "Renhold", "Leie", "Fellesutgifter", 
    "Annen", "Renovasjon", "Reparasjon", "MST"
}

def parse_01_txt(filepath: str):
    transactions = []
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            parts = line.split()
            if len(parts) < 6: continue
            
            # Amount is always the last token
            amount_str = parts[-1]
            try:
                # Handle possible comma as decimal separator
                amount = float(amount_str.replace(',', '.'))
            except:
                continue
                
            # Entity ID is usually the first digit-only block after index 2
            entity_id = None
            entity_id_idx = -1
            for i in range(3, len(parts)):
                if parts[i].isdigit() and len(parts[i]) >= 5:
                    entity_id = parts[i]
                    entity_id_idx = i
                    break
            
            if not entity_id:
                continue
            
            # Extract name tokens
            name_parts = []
            for i in range(entity_id_idx + 1, len(parts) - 1):
                p = parts[i]
                # Stop heuristics
                if p.isdigit() and len(p) >= 4: break
                if p in STOP_TOKENS: break
                name_parts.append(p)
            
            entity_name = " ".join(name_parts).strip()
            if not entity_name:
                continue
                
            transactions.append({
                "name": entity_name,
                "id": entity_id,
                "amount": amount,
                "line": line
            })
            
    return transactions

async def run_import(filepath: str, dry_run=False):
    transactions = parse_01_txt(filepath)
    print(f"Parsed {len(transactions)} transactions from {filepath}")
    
    # Group by name
    grouped = {}
    for tx in transactions:
        name = tx['name']
        if name not in grouped:
            grouped[name] = {"total_amount": 0.0, "transactions": []}
        grouped[name]["total_amount"] += tx["amount"]
        grouped[name]["transactions"].append(tx)
        
    print(f"Found {len(grouped)} unique entities in file.")
    
    async with SessionLocal() as db:
        res = await db.execute(select(Property))
        all_props = res.scalars().all()
        
        matches = 0
        total_matched_amount = 0.0
        
        for name, data in grouped.items():
            best_prop = None
            best_score = 0.0
            
            for p in all_props:
                score = similar(name, p.name)
                if score > best_score:
                    best_score = score
                    best_prop = p
            
            if best_score >= 0.90: # Higher threshold
                print(f"MATCH: '{name}' -> '{best_prop.name}' (Score: {best_score:.2f}, Amount: {data['total_amount']:.2f})")
                
                if not dry_run:
                    if not best_prop.external_data:
                        best_prop.external_data = {}
                    
                    fin = best_prop.external_data.get('financials', {})
                    if not isinstance(fin, dict): fin = {}
                    
                    # Store transactions
                    fin['transactions_2024'] = data['transactions']
                    fin['total_spend_2024'] = data['total_amount']
                    fin['last_updated_erp'] = '2026-01-05'
                    
                    best_prop.external_data['financials'] = fin
                    
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(best_prop, "external_data")
                    db.add(best_prop)
                    
                matches += 1
                total_matched_amount += data['total_amount']
            else:
                if best_score > 0.6:
                    print(f"SOFT MATCH (IGNORED): '{name}' -> '{best_prop.name}' (Score: {best_score:.2f})")
                # else: print(f"NO MATCH: '{name}'")
        
        if not dry_run:
            await db.commit()
            print(f"\nSUCCESS: Updated {matches} properties with {total_matched_amount:.2f} total spend.")
        else:
            print(f"\nDRY RUN: Would update {matches} properties with {total_matched_amount:.2f} total spend.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to 01.txt")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(run_import(args.file, args.dry_run))
