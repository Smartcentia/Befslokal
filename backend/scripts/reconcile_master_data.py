
import pandas as pd
import os
import json
import re
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

def fuzzy_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

class ReconciliationEngineV12:
    def __init__(self, storage_dir: str, output_dir: str):
        self.storage_dir = storage_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.run_id = str(uuid.uuid4())[:8]
        self.audit_log = []

    def log_event(self, event: str, details: Any):
        print(f"[{event}] {details}")
        self.audit_log.append({
            "event": event, 
            "details": details, 
            "timestamp": str(pd.Timestamp.now()),
            "run_id": self.run_id
        })

    def generate_id(self, *args) -> str:
        """Generates a stable deterministic hash ID from components."""
        seed = "|".join([str(a).strip().lower() for a in args])
        return hashlib.sha1(seed.encode()).hexdigest()[:12]

    def normalize_address(self, addr: str) -> str:
        """Standardizes address for mapping (v1.2 refined)."""
        if not addr or pd.isna(addr): return ""
        addr = str(addr).lower()
        addr = addr.split(',')[0].strip()
        addr = addr.split(' avd')[0].strip()
        # Handle floor info specifically
        addr = re.sub(r'\d+\. ?etg', '', addr)
        # Standardize abbreviations
        addr = re.sub(r'[\.\-\s]+', ' ', addr).strip()
        addr = addr.replace('gate ', 'gt ').replace('veien ', 'v ').replace('vegen ', 'v ')
        return addr

    def normalize_name(self, name: str) -> str:
        """Standardizes names for overlap matching."""
        if not name or pd.isna(name): return ""
        name = str(name).lower()
        removals = ['avd.', 'avdeling', 'enhet', 'adm', 'administrasjon', 'region', 'senter', 'ungdomssenter', 'familievernkontor', 'fvk']
        for r in removals:
            name = name.replace(r, '')
        name = re.sub(r'[^\w\s]', ' ', name)
        return " ".join(name.split())

    def ingest_sources(self):
        """Loads harvested datasets."""
        self.log_event("INGEST_START", "Loading v1.2 Refined datasets")
        
        # 1. BIRK
        birk_path = os.path.join(self.storage_dir, "birk_raw.csv")
        birk = pd.read_csv(birk_path)
        birk['birk_enhet_id'] = birk['EnhetID'].astype(str)
        
        # 2. Address Catalog
        addr_files = [f for f in os.listdir(self.storage_dir) if f.startswith("address_") and f.endswith(".csv")]
        addr_list = []
        for f in addr_files:
            try:
                df = pd.read_csv(os.path.join(self.storage_dir, f))
                if 'Gateadresse' not in df.columns:
                     df = pd.read_csv(os.path.join(self.storage_dir, f), names=['Gateadresse', 'Poststed', 'Dummy', 'Postnummer', 'Kontakt'], skiprows=1)
                addr_list.append(df)
            except Exception as e:
                self.log_event("INGEST_ERROR", f"Failed to load {f}: {e}")
        
        addr_cat = pd.concat(addr_list, ignore_index=True) if addr_list else pd.DataFrame()
        
        # 3. Portfolio
        portfolio_path = os.path.join(self.storage_dir, "portfolio_raw.csv")
        portfolio = pd.read_csv(portfolio_path, sep=';')
        
        # Apply Node Master ID Logic
        # PROPERTY ID Strategy: Matrikkel or Address Hash
        portfolio['property_key'] = portfolio.apply(
            lambda row: self.generate_id(row['Property-Address'], row['Property-Zip']), axis=1
        )
        # CONTRACT ID Strategy: Hash of key fields
        portfolio['contract_id'] = portfolio.apply(
            lambda row: self.generate_id(row['EOM-Property-Id'], row['Lieu-Name'], "v1.2"), axis=1
        )
        
        return birk, addr_cat, portfolio

    def run_reconciliation(self):
        birk, addr_cat, portfolio = self.ingest_sources()
        
        # Normalization
        birk['addr_norm'] = birk['Adresse'].apply(self.normalize_address)
        birk['postnr_str'] = birk['Postnr'].astype(str).str.zfill(4).str.replace(r'\.0$', '', regex=True)
        birk['name_norm'] = birk['Navn'].apply(self.normalize_name)
        
        addr_cat['addr_norm'] = addr_cat['Gateadresse'].apply(self.normalize_address)
        addr_cat['postnr_str'] = addr_cat['Postnummer'].astype(str).str.zfill(4).str.replace(r'\.0$', '', regex=True)
        addr_cat['contact_norm'] = addr_cat['Kontakt'].apply(self.normalize_name)
        
        portfolio['addr_norm'] = portfolio['Property-Address'].apply(self.normalize_address)
        portfolio['postnr_str'] = portfolio['Property-Zip'].astype(str).str.zfill(4).str.replace(r'\.0$', '', regex=True)
        portfolio['name_norm'] = portfolio['Lieu-Name'].apply(self.normalize_name)

        address_audit = []
        birk_property_audit = []
        crosswalk_edges = []

        # --- STEP 1: Address Enrichment (Address Catalog -> BIRK) ---
        for _, b_row in birk.iterrows():
            candidates = addr_cat[addr_cat['postnr_str'] == b_row['postnr_str']]
            best_score, best_match = 0, None
            
            # Check for multiple contacts at same address (Collision logic)
            potential_contacts = []
            for _, a_row in candidates.iterrows():
                addr_score = fuzzy_ratio(b_row['addr_norm'], a_row['addr_norm'])
                name_score = fuzzy_ratio(b_row['name_norm'], a_row['contact_norm'])
                score = (addr_score * 0.7) + (name_score * 0.3)
                
                if score > 0.8:
                    potential_contacts.append((score, a_row))
                if score > best_score:
                    best_score, best_match = score, a_row

            # Collision: multiple high-scoring contacts for one BIRK unit
            collision = len([c for c in potential_contacts if c[0] > 0.85]) > 1

            address_audit.append({
                "BIRK_ID": b_row['birk_enhet_id'],
                "BIRK_Name": b_row['Navn'],
                "Enriched_Addr": best_match['Gateadresse'] if (best_match is not None and best_score > 0.9) else b_row['Adresse'],
                "Score": round(best_score, 4),
                "Collision": collision,
                "Confidence": "HIGH" if (best_score > 0.93 and not collision) else ("MEDIUM" if best_score > 0.8 else "LOW"),
                "Status": "approved" if (best_score > 0.93 and not collision) else "pending"
            })

        # --- STEP 2: LOCATED_AT (BIRK -> PROPERTY) ---
        for _, b_row in birk.iterrows():
            candidates = portfolio[portfolio['postnr_str'] == b_row['postnr_str']]
            potential_edges = []
            
            for _, p_row in candidates.iterrows():
                addr_score = fuzzy_ratio(b_row['addr_norm'], p_row['addr_norm'])
                name_score = fuzzy_ratio(b_row['name_norm'], p_row['name_norm'])
                score = (addr_score * 0.6) + (name_score * 0.4)
                
                if score > 0.6:
                    potential_edges.append((score, p_row))

            potential_edges.sort(key=lambda x: x[0], reverse=True)
            
            if potential_edges:
                best_score, best_p = potential_edges[0]
                collision = len([e for e in potential_edges if e[0] > 0.85]) > 1
                
                edge = {
                    "source_type": "BIRK",
                    "source_id": b_row['birk_enhet_id'],
                    "target_type": "PROPERTY",
                    "target_id": best_p['property_key'],
                    "relation_type": "LOCATED_AT",
                    "match_method": "heuristic",
                    "score": round(best_score, 4),
                    "confidence": "HIGH" if (best_score > 0.93 and not collision) else "LOW",
                    "status": "approved" if (best_score > 0.93 and not collision) else "pending",
                    "collision_flag": collision,
                    "run_id": self.run_id
                }
                crosswalk_edges.append(edge)
                birk_property_audit.append({**edge, "BIRK_Name": b_row['Navn'], "Prop_Addr": best_p['Property-Address']})

        # Output Results
        pd.DataFrame(address_audit).to_csv(os.path.join(self.output_dir, "address_match_audit.csv"), index=False)
        pd.DataFrame(birk_property_audit).to_csv(os.path.join(self.output_dir, "birk_property_audit.csv"), index=False)
        
        crosswalk_df = pd.DataFrame(crosswalk_edges)
        crosswalk_df.to_csv(os.path.join(self.output_dir, "master_crosswalk_audit.csv"), index=False)
        
        # Approval Queue for Manual Review (v1.2)
        # Includes all 'pending' edges or collisions
        pending_queue = crosswalk_df[crosswalk_df['status'] == 'pending'].copy()
        pending_queue['manual_approval'] = "" # Placeholder for user (approve/reject)
        pending_queue['manual_comment'] = ""
        pending_queue.to_csv(os.path.join(self.output_dir, "approval_queue_pending.csv"), index=False)

        # NODE MASTER Output (Clean)
        birk.to_csv(os.path.join(self.output_dir, "birk_clean.csv"), index=False)
        portfolio.to_csv(os.path.join(self.output_dir, "property_master.csv"), index=False)
        
        # Coverage Reporting (run_log.json)
        # BIRK -> Property Coverage
        total_birk = len(birk)
        mapped_birk = crosswalk_df[crosswalk_df['source_type'] == 'BIRK']['source_id'].nunique()
        
        # Properties without BIRK (Partial Linkage)
        total_props = len(portfolio)
        mapped_props = crosswalk_df[crosswalk_df['target_type'] == 'PROPERTY']['target_id'].nunique()
        
        run_log = {
            "run_id": self.run_id,
            "timestamp": str(pd.Timestamp.now()),
            "metrics": {
                "birk_to_property_coverage": {
                    "total_birk_units": total_birk,
                    "mapped_units": mapped_birk,
                    "coverage_rate": round(mapped_birk / total_birk, 4) if total_birk > 0 else 0
                },
                "property_utilization": {
                    "total_properties": total_props,
                    "properties_with_units": mapped_props,
                    "vacant_or_admin_properties": total_props - mapped_props
                },
                "validation_stats": {
                    "approved_count": len(crosswalk_df[crosswalk_df['status'] == 'approved']),
                    "pending_review_count": len(crosswalk_df[crosswalk_df['status'] == 'pending']),
                    "collision_count": int(crosswalk_df['collision_flag'].sum())
                }
            },
            "status": "SUCCESS (Phase 4 Blocked)"
        }
        
        with open(os.path.join(self.output_dir, "run_log.json"), "w") as f:
            json.dump(run_log, f, indent=2)

        self.log_event("AUDIT_COMPLETE", f"Produced v1.2 artifacts (Edges: {len(crosswalk_edges)})")
        return len(crosswalk_edges)

if __name__ == "__main__":
    storage_path = "/tmp/audit_v1.1"
    output_path = "/tmp/audit_v1.1/results"
    
    engine = ReconciliationEngineV12(storage_path, output_path)
    count = engine.run_reconciliation()
    print(f"\nFinal Audit v1.2 Edge Count: {count}")
    print(f"Artifacts generated in: {output_path}")
