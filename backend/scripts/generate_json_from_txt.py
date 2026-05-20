
import json
import os
import re

def parse_txt_to_dict(path, sep='\t'):
    if not os.path.exists(path):
        return []
    # Using utf-8 with ignore for safety, though hex confirmed utf-8
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    if not lines:
        return []
    
    headers = [h.strip() for h in lines[0].strip().split(sep)]
    data = []
    for line in lines[1:]:
        if not line.strip():
            continue
        vals = line.strip().split(sep)
        row = dict(zip(headers, vals + [''] * (max(0, len(headers) - len(vals)))))
        data.append(row)
    return data

def normalize_id(val):
    if val is None: return None
    s = str(val).strip()
    if not s or s.lower() in ["nan", "none", "null"]: return None
    if re.fullmatch(r"[-+]?\d+\.0", s):
        return s.rsplit('.0', 1)[0]
    return s

def clean_name(name):
    if not name: return ""
    name = name.lower()
    name = re.sub(r"^\d+\s*-\s*", "", name)
    replacements = {
        "kontoret": "kontor",
        "familievern-kontoret": "familievernkontor",
        "familievernkontoret": "familievernkontor",
        "ungdomshjem": "ungdomssenter",
        "v/": "", ",": " ", ".": " ", "-": " "
    }
    for old, new in replacements.items(): name = name.replace(old, new)
    words = [w for w in name.split() if w not in ["i", "på", "og", "av", "til"]]
    return " ".join(words).strip()

def generate_hierarchical_json():
    totalny_path = "/Users/frank/Documents/BEFS_CLEAN/backend/docs/totalny.txt"
    edon2_path = "/Users/frank/Documents/BEFS_CLEAN/finans/e-don2.txt"
    output_path = "/Users/frank/Documents/BEFS_CLEAN/docs/database_eksport_relasjoner.json"

    print(f"Laster kildedata (UTF-8)...")
    totalny = parse_txt_to_dict(totalny_path, '\t')
    edon = parse_txt_to_dict(edon2_path, '\t')

    # 1. Map ALL units from EDON (this is our canonical hierarchy)
    all_nodes = {}
    for row in edon:
        uid = normalize_id(row.get('EnhetID'))
        if not uid: continue
        all_nodes[uid] = {
            "unit_id_erp": uid,
            "name": row.get('Enhetsnavn', 'Ukjent'),
            "parent_unit_id_erp": normalize_id(row.get('TilhørighetEnhetID')),
            "type": row.get('Enhetskorttype', ''),
            "lokasjonskode": normalize_id(row.get('Lokasjonskode')),
            "is_operational": False, # Will be set if found in totalny
            "units": [],
            "avdelinger": []
        }

    # 2. Enrich nodes with data from totalny
    # totalny link is usually via Lokasjonskode or Name
    edon_by_cleaned_name = {clean_name(n["name"]): n for n in all_nodes.values()}
    edon_by_lok = {n["lokasjonskode"]: n for n in all_nodes.values() if n["lokasjonskode"]}

    unmapped_totalny = []
    for row in totalny:
        raw_lok = row.get('Lokalisering', '')
        lok_id = normalize_id(raw_lok.split(' - ')[0] if ' - ' in raw_lok else raw_lok)
        
        # Finding the node in our EDON map
        target_node = edon_by_lok.get(lok_id)
        if not target_node:
            cn = clean_name(row.get('Avtalenavn')) or clean_name(row.get('Lokalisering'))
            target_node = edon_by_cleaned_name.get(cn)
        
        if not target_node:
            # Fallback: create an operational node if not in EDON
            node_id = f"LOK_{lok_id}" if lok_id else f"RAW_{len(unmapped_totalny)}"
            target_node = {
                "unit_id_erp": None,
                "property_id": lok_id,
                "name": row.get('Avtalenavn', row.get('Lokalisering', 'Ukjent')),
                "parent_unit_id_erp": None,
                "is_operational": True,
                "units": [],
                "avdelinger": []
            }
            unmapped_totalny.append(target_node)
        else:
            target_node["is_operational"] = True
            target_node["property_id"] = lok_id # Store the totalny ID

        # Build contract/unit info
        contract = {
            "elements_id": row.get('Elements ', 'N/A'),
            "purpose": row.get('Målgruppe', ''),
            "area": row.get('Areal', ''),
            "rent": row.get('KPI-justert kontraktsleie til okt 2025', ''),
            "start": row.get('Startdato', ''),
            "end": row.get('Sluttdato', ''),
            "landlord": row.get('Utleier', '')
        }
        target_node["units"].append(contract)

    # 3. Assemble Tree
    assigned = set()
    all_combined = list(all_nodes.values()) + unmapped_totalny
    node_map = {n.get("unit_id_erp") or n.get("property_id"): n for n in all_combined}

    for n in all_combined:
        pid = n.get("parent_unit_id_erp")
        curr_id = n.get("unit_id_erp") or n.get("property_id")
        if pid and pid in node_map and pid != curr_id:
            node_map[pid]["avdelinger"].append(n)
            assigned.add(curr_id)

    roots = [n for n in all_combined if (n.get("unit_id_erp") or n.get("property_id")) not in assigned]

    # Final Output
    output = {
        "export_date": "2024-02-26",
        "description": "Fullstendig organisatorisk og operasjonelt hierarki (Bufdir -> Region -> Eiendom)",
        "metadata": {
            "total_nodes": len(all_combined),
            "roots": len(roots),
            "operational_nodes": len([n for n in all_combined if n.get("is_operational")]),
            "unmapped_from_erp": len(unmapped_totalny)
        },
        "properties": roots
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Suksess! Eksporterte {len(all_combined)} noder.")
    print(f"Hierarki: {len(roots)} topp-noder og {len(assigned)} under-enheter.")
    print(f"Endelig fil: {output_path}")

if __name__ == "__main__":
    generate_hierarchical_json()
