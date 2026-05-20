from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from pydantic import BaseModel

from app.api.deps import get_current_active_superuser
from app.domains.core.models.user import User

# Import based on execution context
try:
    from app.services.glossary_service import run_glossary_scan
except ImportError:
    # Fallback for script execution or different python path
    try:
        from backend.app.services.glossary_service import run_glossary_scan
    except ImportError:
         print("Warning: Could not import glossary_service")

router = APIRouter()

# Configuration
# Assuming standard backend structure: backend/app/api/v1/endpoints/glossary.py
# Data is in backend/data
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
GLOSSARY_FILE = BASE_DIR / "data" / "glossary_terms.json"
USAGE_FILE = BASE_DIR / "data" / "term_usage_report.json"

class TermUsage(BaseModel):
    term: str
    file: str
    line: int
    context: str

class GlossaryTerm(BaseModel):
    term: str
    definition: str
    tags: Optional[List[str]] = []
    usage: Optional[List[TermUsage]] = []

@router.get("", response_model=List[GlossaryTerm])
def get_glossary():
    """
    Retrieve all glossary terms merged with their usage scan results.
    """
    # Load terms
    terms_data = []
    if GLOSSARY_FILE.exists():
        try:
            with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
                terms_data = json.load(f)
        except Exception as e:
            print(f"Error loading terms: {e}")
            
    # Load usage
    usage_map = {}
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                usage_data = json.load(f)
                # Group by term
                for item in usage_data:
                    term_key = item.get("term")
                    if term_key:
                        if term_key not in usage_map:
                            usage_map[term_key] = []
                        usage_map[term_key].append(item)
        except Exception as e:
            print(f"Error loading usage report: {e}")
    
    # Merge
    result = []
    for t in terms_data:
        # Create a copy to avoid modifying the original if cached
        term_obj = t.copy()
        term_obj["usage"] = usage_map.get(t.get("term"), [])
        result.append(term_obj)
        
    return result

@router.post("/scan")
def scan_glossary_terms(_: User = Depends(get_current_active_superuser)):
    """
    Triggers a scan of the codebase for glossary terms. Admin only.
    """
    try:
        # Re-import to ensure we have the function if it failed initially or wasn't needed
        try:
            from app.services.glossary_service import run_glossary_scan
        except ImportError:
            from backend.app.services.glossary_service import run_glossary_scan
            
        result = run_glossary_scan()
        if result["status"] == "error":
             raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
