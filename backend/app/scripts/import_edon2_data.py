import sys
import os
import asyncio
from dotenv import load_dotenv

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(BACKEND_DIR)

# Load environment variables
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

from app.db.session import SessionLocal
from app.services.data_management import DataManagementService
# Imports to ensure SQLAlchemy models are registered
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.core.models.center import Center
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.models.file_meta import FileMeta
from app.domains.core.models.user import User
from app.domains.core.models.audit import AuditLog

async def run_import():
    # Detect all potential source files
    source_files = ['e-don2.txt', 'e-dom.txt', 'e-don.txt', 'e-dom2.txt']
    
    all_contents = []
    files_loaded = []
    
    print("Multi-Source Data Discovery:")
    for filename in source_files:
        p = os.path.join(BACKEND_DIR, filename)
        if not os.path.exists(p):
            continue
            
        print(f"Reading {p}...")
        try:
            with open(p, 'rb') as f:
                content = f.read()
                if not content: continue
                
                # SEARCH DIAGNOSTIC in this file
                print(f"  - SEARCH DIAGNOSTIC ({filename}):")
                search_targets = [b"1217", b"Lamo"]
                for target in search_targets:
                    if target in content:
                        print(f"    - '{target.decode()}' FOUND!")
                    else:
                        print(f"    - '{target.decode()}' NOT FOUND.")

                all_contents.append(content)
                files_loaded.append(filename)
                print(f"  - Loaded {filename} ({len(content)} bytes)")
        except Exception as e:
            print(f"  - Error reading {filename}: {e}")

    if not all_contents:
        print("Error: No valid source files found in backend/ directory.")
        return

    print(f"\nCollected {len(files_loaded)} files for multi-source import.")
    print("-" * 40 + "\n")

    print(f"Starting Multi-Source Property Matching (v2.3) import...")
    
    async with SessionLocal() as db:
        service = DataManagementService()
        result = await service.import_edon2_csv(db, all_contents)
        
        if result["status"] == "success":
            print(f"Import Successful!")
            print(f"Updated properties: {result.get('updated', 0)}")
            print(f"Audit log created: match_audit_log.csv")
        else:
            print(f"Import Failed: {result.get('message')}")
            
    print(f"Total entries processed: {len(all_contents)}")

if __name__ == "__main__":
    asyncio.run(run_import())
