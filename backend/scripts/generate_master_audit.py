
import pandas as pd
import os
import json
from typing import List, Dict, Any

class MasterAuditGenerator:
    def __init__(self, manifest_path: str, output_dir: str):
        self.manifest_path = manifest_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def load_data(self):
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def generate_address_audit(self, data: Dict):
        """Generates address_match_audit.csv (BIRK vs Address Catalog)"""
        birk = pd.DataFrame(data['birk_segments'])
        addr = pd.DataFrame(data['address_catalog_segments'])
        
        # Heuristic: Normalize for matching
        birk['addr_norm'] = birk['StreetAddress'].str.lower().str.split(',').str[0].str.strip()
        addr['addr_norm'] = addr['StreetAddress'].str.lower().str.split(',').str[0].str.strip()
        
        audit_rows = []
        for _, b_row in birk.iterrows():
            matches = addr[addr['addr_norm'] == b_row['addr_norm']]
            
            if len(matches) == 0:
                status, score, conf = "UNMATCHED", 0.0, "LOW"
            elif len(matches) == 1:
                status, score, conf = "EXACT_1to1", 1.0, "HIGH"
            else:
                status, score, conf = "AMBIGUOUS_1toN", 0.5, "MEDIUM"
                
            audit_rows.append({
                "source_type": "BIRK",
                "source_id": b_row['EnhetID'],
                "source_name": b_row['UnitName'],
                "address": b_row['StreetAddress'],
                "match_method": status,
                "score": score,
                "confidence": conf,
                "match_details": f"Found {len(matches)} potential targets in Address Catalog"
            })
            
        df = pd.DataFrame(audit_rows)
        # In a real environment, we'd save this. Here we print for log.
        print("\n--- ADDRESS MATCH AUDIT ---")
        print(df.to_string())
        return df

if __name__ == "__main__":
    gen = MasterAuditGenerator("backend/data/clean/master_data_discovery.json", "backend/data/audit")
    gen.generate_address_audit(gen.load_data())
