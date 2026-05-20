
import asyncio
import sys
import os
import json
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Related models
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

PROVIDERS_MAP = {
    "Håkonsgate 4 AS": "Håkonsgate 4",
    "Isbjørn Eiendom AS": "Enhet for inntak", 
    "Femur Eiendom AS": "Harstad",
    "Varanger ASVO AS": "Vadsø",
    "Vesterålen Eiendom AS": "Lofoten og Vesterålen",
    "Løkkeveien 33 AS": "Alta",
    "Busch-Sørensen Rengjøringsbyrå AS, Bodø": "Bodø",
    "Storgata 70": "Storgata 70",
    "Løkkeveien 33": "Løkkeveien 33",
    "Fitnodatgeaidnu": "Fitnodatgeaidnu",
    "Sørøygt 10": "Sørøygt 10",
    "Wiulls gate 3": "Wiulls gate 3",
    "Nordstrandveien 41": "Nordstrandveien 41",
    "Harila Eiendom AS": "Vadsø",
    "Narvik Havn KF": "Narvik",
    "Enhet for spesialiserte fosterhjem": "Enhet for spesialiserte fosterhjem",
    "Sollia barne- og ungdomssenter miljøavdeling": "Sollia barne- og ungdomssenter + fosterhjemstjenesten",
    "Pirsenteret": "Regionkontor felleskostnader", # Specific to Midt-Norge admin hub if needed, but pirsenteret is the building
    "Bybroen bolig AS": "Vikhovlia akuttsenter",
    "Løkka Eftf. AS": "Humla Akuttsenter",
    "Kvartal 71 AS": "Bufetathus Kristiansand",
    "Grønland 68 AS": "Bufetathus Drammen",
    "Anton Jenssensgate 2 AS": "Bufetathus Tønsberg",
    "LANGSÆVEIEN 6 AS": "Bufetathus Arendal",
    "Kontorbygg AS": "Bufetathus Skien",
    "Heian AS": "Harstad",
    "POLARIS EIENDOMSDRIFT AS": "Hammerfest",
    "MP Steiro Eiendom AS": "Sortland",
    # Region Øst
    "Portalen Kontor AS": "Tærudgata 16",
    "Portalen Forretning AS": "Tærudgata 16",
    "Sandvika Business Center AS": "Elias Smiths vei 22-24",
    "Union Drift Core AS": "Elias Smiths vei 22-24",
    "Smedgata 45 og 49 AS": "Smedgata 49",
    "Østensvikgården AS": "Jernbanevegen 20",
    "Vangsvegen 121 AS": "Vangsvegen 121",
    "Siva FE Kompetansesenteret": "Aumliveien 4C",
    "Lillestrøm Torv AS": "Torget 6",
    "Østre Aker vei 31 AS": "Kabelgata 2",
    "Kvernhuset AS": "Henrik Gerners gate 14",
    "Glemmengaten 55 DA": "Glemmengaten 55",
    "Sentrumskvartalet Askim AS": "Rådhusgata 16",
    "Jessheim Næringspark AS": "Energiveien 14",
    "KB Gruppen Eiendom AS": "Gågata 5",
    "Oscars gate 20 AS": "Oscarsgate 20",
    "OFFENTLIG BYGG HØNEFOSS AS": "Storgata 11",
    "H. Berger Eiendom AS": "Ramsrudveien 32",
    "Lasse Christian Fægri": "Bredalsveien 18",
    "J&B Eiendom AS": "Bjørlistubben 14",
    "Glynitveien 30 AS": "Glynitveien 30",
    "Utleiemegleren Lillestrøm AS": "Vollakrokan 33",
    "OPTA EIENDOM AS": "Grimstadtunet 27",
    "Aarum Eiendom AS": "Sundløkkaveien 73m",
    "VALASKJOLD EIENDOM AS": "Vestrevei 1",
    "Golhus AS": "Strandsagvegen 2",
    "STIFTELSEN DISEN KULTURVEKSTTUN": "Just Brochs gate 13",
    "ARNSTEIN KARLSRUD": "Lundebyveien 363",
    "Grue næringsselskap AS": "Energiveien 13",
    "Bredesen Opset AS": "Frydenlund",
    "Glassbua Kirkenær A.S.": "Jernbaneveien 70",
    "Vestlandske Boligstiftelse AS": "Veslekila 1",
}

def parse_amount(val):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Handle '214 858,-' format
        clean = val.replace(' ', '').replace(',-', '')
        # Handle 1.234,56 vs 1,234.56 - assume挪wegian/European convention if comma is last
        if ',' in clean and '.' not in clean:
            clean = clean.replace(',', '.')
        elif ',' in clean and '.' in clean:
            # Ambiguous, but if we have both, usually comma is decimal in NO
            clean = clean.replace('.', '').replace(',', '.')
        
        # Remove any other non-numeric chars except . and -
        import re
        clean = re.sub(r'[^\d.-]', '', clean)
        try:
            return float(clean)
        except ValueError:
            return 0.0
    return 0.0

async def remap_costs():
    async with SessionLocal() as db:
        res = await db.execute(select(Property))
        all_props = res.scalars().all()
        
        # Build a lookup map property name/address -> Property
        name_map = {}
        for p in all_props:
            name_map[p.name.lower()] = p
            if p.address:
                name_map[p.address.lower()] = p
        
        # Target properties that are "buckets"
        buckets = ["FHT RN - adm", "Regionkontor Nord", "Regionale fellesfunksjoner"]
        
        remapped_count = 0
        
        for p in all_props:
            # We check ALL properties now, but still prioritize known buckets
            fin = p.external_data.get('financials', {})
            expenses = fin.get('manual_expenses', [])
            if not expenses:
                continue
                
            remaining_expenses = []
            moved_any = False
            
            for e in expenses:
                # Search in all metadata
                text_blob = f"{e.get('provider', '')} {e.get('description', '')} {e.get('type', '')} {e.get('category', '')}".lower()
                target_key = None
                for pk, target in PROVIDERS_MAP.items():
                    if pk.lower() in text_blob:
                        target_key = target.lower()
                        break
                
                # Special case for Sollia string merge
                if "sollia" in p.name.lower() and "miljøavdeling" in p.name.lower():
                    target_key = "sollia barne- og ungdomssenter + fosterhjemstjenesten"
                
                if target_key:
                    # Find target property
                    target_prop = None
                    for name, prop in name_map.items():
                        if target_key in name:
                            target_prop = prop
                            break
                    
                    if target_prop and target_prop.property_id != p.property_id:
                        # Move this expense
                        if not target_prop.external_data: target_prop.external_data = {}
                        t_fin = target_prop.external_data.get('financials', {})
                        t_expenses = t_fin.get('manual_expenses', [])
                        t_expenses.append(e)
                        t_fin['manual_expenses'] = t_expenses
                        current_total = parse_amount(t_fin.get('total_manual_expenses', 0))
                        add_amount = parse_amount(e.get('amount', 0))
                        t_fin['total_manual_expenses'] = current_total + add_amount
                        target_prop.external_data['financials'] = t_fin
                        flag_modified(target_prop, "external_data")
                        db.add(target_prop)
                        
                        # Update source total
                        source_total = parse_amount(fin.get('total_manual_expenses', 0))
                        fin['total_manual_expenses'] = source_total - add_amount
                        remapped_count += 1
                        moved_any = True
                        continue
                
                remaining_expenses.append(e)
            
            if moved_any:
                fin['manual_expenses'] = remaining_expenses
                p.external_data['financials'] = fin
                flag_modified(p, "external_data")
                db.add(p)
                
        if remapped_count > 0:
            await db.commit()
            print(f"Successfully remapped {remapped_count} transactions to correct properties.")
        else:
            print("No transactions remapped.")

if __name__ == "__main__":
    asyncio.run(remap_costs())
