import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Any
from sqlalchemy import create_engine, inspect, text, Column
from sqlalchemy.types import JSON

from dotenv import load_dotenv

# Load env before importing settings
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings

# Classification Rules
SENSITIVE_KEYWORDS = ['ssn', 'fnr', 'personnummer', 'credit', 'card', 'password', 'token', 'secret', 'auth', 'salary', 'bank', 'account_number']
FINANCIAL_KEYWORDS = ['amount', 'cost', 'price', 'rent', 'budget', 'expense', 'transaction', 'currency', 'payment', 'invoiced']
PII_KEYWORDS = ['email', 'phone', 'name', 'address', 'user', 'owner', 'tenant']

def classify_field(table: str, column: str, path: str = "") -> str:
    """Classifies a field based on its name and context."""
    full_name = f"{table}.{column}{'.' + path if path else ''}".lower()
    
    if any(k in full_name for k in SENSITIVE_KEYWORDS):
        return "Level 3: Restricted (High Sensitivity)"
    if any(k in full_name for k in FINANCIAL_KEYWORDS):
        return "Level 3: Restricted (Financial)"
    if any(k in full_name for k in PII_KEYWORDS):
        return "Level 3: Restricted (PII)"
    
    # Defaults
    if table in ['users', 'user_property_association', 'sessions', 'audit_logs']:
        return "Level 2: Internal"
    
    return "Level 1: Public/Internal"

def scan_json_structure(connection, table: str, column: str) -> Dict[str, Any]:
    """
    Scans a JSONB column to find all unique keys and basic structure.
    Limits to 100 non-null rows for performance.
    """
    query = text(f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL LIMIT 100")
    result = connection.execute(query)
    
    structure = {}
    
    for row in result:
        data = row[0]
        if isinstance(data, dict):
            _scan_dict(data, structure)
        elif isinstance(data, list):
            # Just scan the first item if it's a list of dicts
            if data and isinstance(data[0], dict):
                _scan_dict(data[0], structure)
                
    return structure

def _scan_dict(data: dict, structure: dict):
    for key, value in data.items():
        if key not in structure:
            structure[key] = {"type": type(value).__name__, "sample": str(value)[:50]}
            if isinstance(value, dict):
                 structure[key]["nested"] = {}
        
        if isinstance(value, dict) and "nested" in structure[key]:
             _scan_dict(value, structure[key]["nested"])

def main():
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    catalog = []
    
    with engine.connect() as conn:
        print(f"Scanning database: {settings.POSTGRES_DB}...")
        
        for table_name in inspector.get_table_names():
            print(f"  Analysing {table_name}...")
            columns = inspector.get_columns(table_name)
            
            for col in columns:
                col_name = col['name']
                col_type = col['type']
                
                # Base classification
                classification = classify_field(table_name, col_name)
                
                entry = {
                    "table": table_name,
                    "column": col_name,
                    "type": str(col_type),
                    "classification": classification,
                    "json_structure": None
                }
                
                # Deep dive for JSON types
                if isinstance(col_type, JSON) or str(col_type) in ('JSON', 'JSONB'):
                    print(f"    Scanning JSONB: {col_name}")
                    structure = scan_json_structure(conn, table_name, col_name)
                    entry['json_structure'] = structure
                    
                    # Re-classify based on found keys
                    if structure:
                        sensitive_keys = []
                        for key in structure.keys():
                            key_class = classify_field(table_name, col_name, key)
                            if "Level 3" in key_class:
                                sensitive_keys.append(f"{key} ({key_class})")
                        
                        if sensitive_keys:
                            entry['classification'] = f"Level 3: Mixed Content ({', '.join(sensitive_keys)})"

                catalog.append(entry)

    # Output Report
    report_path = Path(__file__).parent.parent / "data_catalog.md"
    with open(report_path, "w") as f:
        f.write("# Data Classification Catalog\n\n")
        f.write("| Table | Column | Type | Classification | JSON Content |\n")
        f.write("|---|---|---|---|---|\n")
        
        for item in catalog:
            json_str = ""
            if item['json_structure']:
                # Flatten for display
                keys = list(item['json_structure'].keys())
                json_str = f"`{', '.join(keys[:5])}`" + ("..." if len(keys) > 5 else "")
            
            f.write(f"| **{item['table']}** | {item['column']} | {item['type']} | {item['classification']} | {json_str} |\n")
            
    print(f"\n✅ Scan complete. Catalog written to {report_path}")

if __name__ == "__main__":
    main()
