
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.api.deps import get_db, get_current_active_superuser
from app.services.csv_importer import analyze_import, import_csv_to_db
from app.schemas.import_schema import ImportAnalysisResponse
from app.services.data_management import DataManagementService

router = APIRouter()

@router.post("/analyze", response_model=ImportAnalysisResponse)
async def analyze_csv(
    file: UploadFile = File(...),
    type: str = Query(..., description="Entity type: party, property, contract"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_superuser)
):
    """
    Analyze a CSV file for import.
    Returns detected rows, conflicts, and new columns.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be CSV.")
    
    content = await file.read()
    try:
        analysis = await analyze_import(content, type, db)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing CSV: {str(e)}")

@router.post("/execute")
async def execute_import(
    file: UploadFile = File(...),
    type: str = Query(..., description="Entity type: party, property, contract"),
    update_conflicts: bool = Query(False, description="Whether to overwrite existing records"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_superuser)
):
    """
    Execute CSV import.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be CSV.")
        
    content = await file.read()
    try:
        result = await import_csv_to_db(content, type, db, update_conflicts)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing import: {str(e)}")

@router.post("/edon2")
async def import_edon2(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_superuser)
):
    """
    Import or update property data from e-don2.txt format.
    Focuses on institutional data, budgeted places, and legal bases.
    """
    content = await file.read()
    try:
        result = await DataManagementService.import_edon2_csv(db, content)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing e-don2: {str(e)}")
