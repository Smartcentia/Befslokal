from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.api import deps
from app.services.external.brreg_service import brreg_service
from app.services.financial_import_service import financial_import_service

router = APIRouter()

@router.get("/brreg/{org_number}", response_model=Dict[str, Any])
async def lookup_brreg_unit(
    org_number: str,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lookup organization details in BRREG.
    """
    details = await brreg_service.get_enhet(org_number)
    if not details:
        raise HTTPException(status_code=404, detail="Organization not found")
    return details

@router.post("/import/financials", response_model=Dict[str, Any])
async def import_financial_data(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    # current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Import financial data from CSV/Excel.
    """
    contents = await file.read()
    parsed_data = financial_import_service.parse_financial_file(contents, file.filename)
    
    if not parsed_data:
        raise HTTPException(status_code=400, detail="Could not parse file")
        
    result = financial_import_service.import_expenses(db, parsed_data)
    return result
