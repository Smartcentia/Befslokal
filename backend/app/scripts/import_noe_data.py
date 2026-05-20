
import asyncio
import sys
import os
import re
from sqlalchemy import select
from dotenv import load_dotenv
from difflib import get_close_matches

# Path setup
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import other models to ensure registry is populated
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

KNOWN_CATEGORIES = [
    "Barnevernsinstitusjoner",
    "Fosterhjemstjenesten",
    "Regionale fellesfunksjoner",
    "Sentre for foreldre og barn",
    "Familieverntjeneste",
    "Omsorgssentre for mindreårige",
    "Statlig regionalt barnevernmyndighet",
    "Beredskapshjem",
    "Inntak",
    "Fosterhjem",
    "Hjelpetiltak i hjemmet"
]

KNOWN_COST_TYPES = [
    "Strøm og oppvarming",
    "Renhold lokaler",
    "Leie lokaler andre utleiere",
    "Renovasjon, vann, avløp o.l.",
    "Reparasjon og vedlikehold leide lokaler",
    "Fellesutgifter andre utleiere",
    "Annen kostnad lokaler",
    "Leie lokaler fra Statsbygg",
    "Fellesutgifter (BAD) Statsbygg",
    "Fellesutgifter Statsbygg - indre vedlikehold",
    "Fellesutgifter Statsbygg",
    "Vakthold lokaler",
    "Leie parkeringsplass",
    "Inventar og utstyr",
    "Drift av IKT/telefon mm.",
    "Juridisk bistand",
    "Kjøp av andre tjenester",
]

INPUT_FILE = "backend/docs/noe.txt"

async def import_data():
    print("Starting import of noe.txt...")
    
    async with SessionLocal() as session:
        session.expire_on_commit = False # Prevent MissingGreenlet on property access after batch commit
        # Load all properties
        stmt = select(Property)
        result = await session.execute(stmt)
        properties = result.scalars().all()
        print(f"Loaded {len(properties)} properties from DB.")
        
        # Build Maps
        id_map = {}
        name_map = {}
        
        for p in properties:
            ext = p.external_data or {}
            fin = ext.get('financials', {})
            dim2 = fin.get('Dim 2(T)') or fin.get('Dim 2')
            if dim2:
                id_map[str(dim2)] = p
            
            # Normalize Name for fuzzy matching (simple lowercase)
            if p.name:
                name_map[p.name.lower().strip()] = p
                
        print(f"Mapped {len(id_map)} properties by Dim 2 ID.")
        
        # Parse File
        with open(INPUT_FILE, 'r') as f:
            lines = f.readlines()
            
        matches = 0
        updates = 0
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            
            # Basic parsing
            # Regex: Region(Group1) ID(Group2) Middle(Group3) Amount(Group4)
            match = re.search(r'^(.*?) (\d{6}) (.*) ((-?[\d]+,[\d]+)|(-?[\d]+))$', line)
            if not match:
                continue
                
            region_part = match.group(1).strip()
            prop_id = match.group(2).strip()
            middle = match.group(3).strip()
            amount_str = match.group(4).strip().replace(',', '.')
            try:
                amount = float(amount_str)
            except:
                print(f"Error parsing amount line {line_idx+1}: {amount_str}")
                continue
                
            # Parse Middle section using Categories
            category = None
            prop_name_in_file = None
            cost_vendor_chunk = None
            
            for cat in sorted(KNOWN_CATEGORIES, key=len, reverse=True):
                if cat in middle:
                    parts = middle.rpartition(cat)
                    prop_name_in_file = parts[0].strip()
                    category = cat
                    cost_vendor_chunk = parts[2].strip()
                    break
            
            if not category:
                # If no category found, likely bad line. Skip and log slightly less verbose or just skip
                # print(f"Skipping line {line_idx+1}: No Category found.")
                continue
                
            # Parse Cost Vendor Chunk
            cost_type = None
            vendor = None
            
            for ct in sorted(KNOWN_COST_TYPES, key=len, reverse=True):
                if cost_vendor_chunk.startswith(ct):
                    cost_type = ct
                    vendor = cost_vendor_chunk[len(ct):].strip()
                    break
            
            if not cost_type:
                 cost_type = "Uncategorized"
                 vendor = cost_vendor_chunk
            
            # Find Property
            target_prop = None
            
            # 1. Try ID
            if prop_id in id_map:
                target_prop = id_map[prop_id]
            
            # 2. Try Name Match (Exact)
            if not target_prop:
                if prop_name_in_file.lower() in name_map:
                    target_prop = name_map[prop_name_in_file.lower()]
            
            # 3. Fuzzy match
            if not target_prop:
                try:
                    candidates = list(name_map.keys())
                    matches_fuzzy = get_close_matches(prop_name_in_file.lower(), candidates, n=1, cutoff=0.55) 
                    # 0.55 cutoff to be somewhat permissive but avoiding total garbage
                    if matches_fuzzy:
                        best_match_name = matches_fuzzy[0]
                        target_prop = name_map[best_match_name]
                        # Log the fuzzy match to see what happened
                        print(f"Fuzzy Match: '{prop_name_in_file}' -> '{target_prop.name}' (ID: {prop_id})")
                except Exception as e:
                    print(f"Fuzzy match error: {e}")
            
            if target_prop:
                matches += 1
                
                # Setup financial structure
                if not target_prop.external_data: target_prop.external_data = {}
                # Ensure financials dict exists
                fin_data = target_prop.external_data.get('financials', {})
                target_prop.external_data['financials'] = fin_data
                
                # Ensure manual_expenses list exists
                manual_items = fin_data.get('manual_expenses', [])
                fin_data['manual_expenses'] = manual_items
                
                # Check for duplicates using content hash logic
                is_duplicate = False
                for existing in manual_items:
                    # Check if exact same entry from noe.txt already exists
                    if (existing.get('source') == 'noe.txt' and 
                        existing.get('amount') == amount and
                        existing.get('description') == (vendor or "Unknown") and
                        existing.get('category') == category):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    expense_item = {
                        "source": "noe.txt",
                        "id_ref": prop_id,
                        "category": category,
                        "account": cost_type,
                        "amount": amount,
                        "description": vendor or "Unknown",
                        "date": "2024-01-01" 
                    }
                    manual_items.append(expense_item)
                    # Update total only for new items
                    current_total = fin_data.get('total_manual_expenses', 0) or 0
                    fin_data['total_manual_expenses'] = current_total + amount
                else:
                    # print(f"Duplicate found for {prop_id}, skipping addition.")
                    pass
                

                
                # Link ID if missing
                if not fin_data.get('Dim 2(T)'):
                     fin_data['Dim 2(T)'] = prop_id
                
                # Explicitly flag dirty - reassigning entire dict to column
                target_prop.external_data = target_prop.external_data.copy() 
                # Note: SQLAlchemy detects JSON changes better with copy or flag_modified.
                # Just reassigning strictly might be enough if tracking.
                
                session.add(target_prop)
                updates += 1
            else:
                # Create new Property if not found
                new_prop = Property(
                    name=prop_name_in_file,
                    address=prop_name_in_file, # Fallback to name as address to satisfy DB constraint
                    postal_code="9999", # Placeholder
                    city="Ukjent Sted", # Placeholder
                    # usage=category # Could map category to usage
                    external_data = {
                        "Dim 2(T)": prop_id,
                        "source": "noe.txt_import",
                        "category_hint": category
                    }
                )
                
                # Add to session immediately so we can link subsequent rows
                session.add(new_prop)
                # Need to flush to get ID? No, UUID is default, but we need object reference.
                # We can add to our local maps.
                
                id_map[str(prop_id)] = new_prop
                name_map[prop_name_in_file.lower().strip()] = new_prop
                
                target_prop = new_prop
                print(f"CREATED: {prop_name_in_file} (ID: {prop_id})")
                
                # Now proceed to add financial data (shared logic)
                matches += 1 # Count as handled
                
                # Setup financial structure (same as above)
                if not target_prop.external_data: target_prop.external_data = {}
                fin_data = target_prop.external_data.get('financials', {})
                target_prop.external_data['financials'] = fin_data
                
                manual_items = fin_data.get('manual_expenses', [])
                fin_data['manual_expenses'] = manual_items
                
                # Check for duplicates (same logic)
                is_duplicate = False
                for existing in manual_items:
                     if (existing.get('source') == 'noe.txt' and 
                        existing.get('amount') == amount and
                        existing.get('description') == (vendor or "Unknown") and
                        existing.get('category') == category):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    expense_item = {
                        "source": "noe.txt",
                        "id_ref": prop_id,
                        "category": category,
                        "account": cost_type,
                        "amount": amount,
                        "description": vendor or "Unknown",
                        "date": "2024-01-01" 
                    }
                    manual_items.append(expense_item)
                    current_total = fin_data.get('total_manual_expenses', 0) or 0
                    fin_data['total_manual_expenses'] = current_total + amount
                
                if not fin_data.get('Dim 2(T)'):
                     fin_data['Dim 2(T)'] = prop_id
                     
                target_prop.external_data = target_prop.external_data.copy()
                updates += 1
        
        try:
            await session.commit()
            print(f"Import Complete. Processed {line_idx+1} lines. Matched {matches} properties/lines. Total Updates: {updates}")
        except Exception as e:
            print(f"Final commit failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(import_data())
