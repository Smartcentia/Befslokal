import logging
from fastapi import APIRouter, Depends, HTTPException, Response, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from pathlib import Path
import os
from pydantic import BaseModel
from typing import Optional, List

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.core.property_access import check_property_access
from app.models.file_meta import FileMeta
# Assumes storage service exists or we implement a simple one
# from app.services.storage import get_storage

router = APIRouter()

from fastapi import UploadFile, File, BackgroundTasks, status, Form
from app.services.storage import get_storage
from app.models.file_meta import FileMeta
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.unit import Unit as UnitModel
import shutil
import uuid
from datetime import datetime
from app.services.search.indexer import index_pdf_file_async

# --- SAS Upload Models ---
class SASRequest(BaseModel):
    filename: str
    content_type: str
    contract_id: Optional[UUID] = None
    tags: Optional[List[str]] = None

class SASResponse(BaseModel):
    file_id: UUID
    upload_url: str # Helper: Full URL with SAS token for PUT request
    blob_path: str   # Internal path to be sent back to /complete

class FileCompleteRequest(BaseModel):
    file_id: UUID
    contract_id: Optional[UUID] = None
    blob_path: str
    filename: str
    content_type: str
    tags: Optional[List[str]] = None

# --- Endpoints ---

@router.post("/upload/sas", response_model=SASResponse)
async def generate_sas_url(
    req: SASRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a write-only SAS URL for direct browser-to-blob upload (med property access check)."""
    # If file is linked to a contract, check property access via contract
    if req.contract_id:
        # Get contract and check property access via unit
        stmt = select(ContractModel).where(ContractModel.contract_id == req.contract_id).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        
        if contract and contract.unit and contract.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(contract.unit.property_id),
                require_write=True
            )
    file_id = uuid.uuid4()
    
    # Determine storage path
    if req.contract_id:
        blob_path = f"contracts/{req.contract_id}/{req.filename}"
    else:
        blob_path = f"uploads/{file_id}/{req.filename}"

    storage = get_storage()
    try:
        sas_url = storage.generate_upload_sas(blob_path, duration_minutes=30)
    except NotImplementedError:
         raise HTTPException(status_code=501, detail="SAS tokens not supported in local storage mode.")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to generate SAS: {str(e)}")

    return SASResponse(
        file_id=file_id,
        upload_url=sas_url,
        blob_path=blob_path
    )

@router.post("/upload/complete", status_code=status.HTTP_201_CREATED)
async def complete_upload(
    req: FileCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registers the uploaded file in DB and triggers indexing (med property access check)."""
    # If file is linked to a contract, check property access via contract
    if req.contract_id:
        # Get contract and check property access via unit
        stmt = select(ContractModel).where(ContractModel.contract_id == req.contract_id).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        
        if contract and contract.unit and contract.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(contract.unit.property_id),
                require_write=True
            )
    
    # 1. Register in DB (FileMeta)
    new_file = FileMeta(
        file_id=req.file_id,
        path=req.blob_path, # We store the relative blob path, NOT the full SAS URL
        content_type=req.content_type,
        tags=req.tags,
        created_at=datetime.utcnow()
    )
    
    if req.contract_id:
        new_file.contract_id = req.contract_id
    
    db.add(new_file)
    try:
        await db.commit()
        await db.refresh(new_file)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    # 2. Trigger Indexing
    indexing_result = None
    if req.content_type == "application/pdf":
        try:
            # Pass UUID object
            indexing_result = await index_pdf_file_async(new_file.file_id, db)
        except Exception as e:
            # We don't fail the request if indexing fails, but we assume the file IS uploaded.
            # In a real system, we might want to check if the blob actually exists first?
            # For now, trust the client has uploaded it.
            logger.error("Indexing failed for %s: %s", new_file.file_id, e)
            # Raise 500 so client knows indexing failed? Or 202 Accepted?
            # Let's return error so UI shows red.
            raise HTTPException(status_code=500, detail=f"File registered but Indexing failed: {e}")

    return {
        "file_id": str(new_file.file_id),
        "path": new_file.path,
        "message": "Upload registered and indexed successfully",
        "indexing_stats": indexing_result
    }

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    contract_id: Optional[UUID] = Form(None), 
    tags: Optional[List[str]] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Last opp fil, lagre i lagringstjeneste og kjør indeksering (OCR) synkront (med property access check)."""
    # If file is linked to a contract, check property access via contract
    if contract_id:
        # Get contract and check property access via unit
        stmt = select(ContractModel).where(ContractModel.contract_id == contract_id).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        result = await db.execute(stmt)
        contract = result.scalar_one_or_none()
        
        if contract and contract.unit and contract.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(contract.unit.property_id),
                require_write=True
            )
    file_id = uuid.uuid4()
    
    if contract_id:
        file_path = f"contracts/{contract_id}/{file.filename}"
    else:
        file_path = f"uploads/{file_id}/{file.filename}"
        
    # Read file content
    content = await file.read()
    
    # Save to Storage (Blob or Local fallback)
    storage = get_storage()
    storage_path = storage.save_file(file_path, content)
    
    # Create Metadata
    # Aligning with app/models/file_meta.py:
    # file_id, contract_id, path, sha256, file_type, content_type, created_at
    new_file = FileMeta(
        file_id=file_id,
        path=storage_path,
        content_type=file.content_type,
        tags=tags,
        # filename and size are not in the model.
        # uploaded_at is created_at in model.
        # We can calculate sha256 if we wanted, but optional.
        # contract_id is optional.
        created_at=datetime.utcnow() 
    )
    
    if contract_id:
        new_file.contract_id = contract_id
    
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    
    indexing_result = None
    # Trigger Indexing (OCR) - SYNC for immediate feedback and safety
    if file.content_type == "application/pdf":
        try:
            # Pass UUID object, not string, as indexer expects UUID
            indexing_result = await index_pdf_file_async(file_id, db)
        except Exception as e:
            # Verify file_id exists in DB
            # Log error but don't fail upload entirely? 
            # Ideally we return 500 if indexing fails so user knows.
            raise HTTPException(status_code=500, detail=f"Upload OK but Indexing failed: {e}")

    return {
        "file_id": str(file_id), 
        "path": storage_path, 
        "message": "Uploaded and Indexed Successfully",
        "indexing_stats": indexing_result
    }


@router.get("/{file_id}/metadata")
async def get_file_metadata(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hent fil metadata (med property access check)."""
    result = await db.execute(select(FileMeta).where(FileMeta.file_id == file_id))
    file_meta = result.scalar_one_or_none()
    
    if not file_meta:
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    
    # Check property access via contract if file is linked to contract
    if file_meta.contract_id:
        stmt = select(ContractModel).where(ContractModel.contract_id == file_meta.contract_id).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        contract_result = await db.execute(stmt)
        contract = contract_result.scalar_one_or_none()
        
        if contract and contract.unit and contract.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(contract.unit.property_id),
                require_write=False
            )
    
    return file_meta

@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Last ned fil (PDF) (med property access check)."""
    result = await db.execute(select(FileMeta).where(FileMeta.file_id == file_id))
    file_meta = result.scalar_one_or_none()
    
    if not file_meta:
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    
    # Check property access via contract if file is linked to contract
    if file_meta.contract_id:
        stmt = select(ContractModel).where(ContractModel.contract_id == file_meta.contract_id).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        contract_result = await db.execute(stmt)
        contract = contract_result.scalar_one_or_none()
        
        if contract and contract.unit and contract.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(contract.unit.property_id),
                require_write=False
            )
    
    # Get file from storage
    storage = get_storage()
    try:
        file_content = storage.get_file(file_meta.path)
        return Response(
            content=file_content,
            media_type=file_meta.content_type or "application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{os.path.basename(file_meta.path)}"'
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fil ikke funnet i storage")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kunne ikke laste ned fil: {str(e)}")

# --- Scanner Endpoint ---
import re

@router.post("/scan", status_code=status.HTTP_200_OK)
async def scan_and_import_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SCANS storage for PDF files, checks if they are imported,
    and tries to link them to Contracts using regex on filenames.
    Pattern: '04-12030-14' (Statsbygg Contract Number)
    Kun ADMIN kan scanne og importere filer.
    """
    # Kun ADMIN kan scanne og importere filer
    from app.domains.core.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can scan and import files"
        )
    storage = get_storage()
    
    # 1. List all blobs
    try:
        # We start with "files/" or root? Let's scan everything for now or logic to skip
        # Assuming user uploads to a specific "dropzone" folder or just root.
        # Let's scan root.
        blobs = storage.list_blobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage list failed: {e}")

    if not blobs:
        return {"message": "No blobs found in storage", "scanned": 0, "imported": 0}

    # 2. Cache Contracts for lookup (Optimize: Don't query inside loop)
    # Fetch all contracts that have 'external_data'
    # We want a map:  "04-12030-14" -> contract_id
    contract_result = await db.execute(select(ContractModel))
    contracts = contract_result.scalars().all()
    
    contract_map = {} # "04-12030-14" -> uuid
    for c in contracts:
        if c.external_data and isinstance(c.external_data, dict):
             c_num = c.external_data.get("contract_number")
             if c_num:
                 contract_map[str(c_num).strip()] = c.contract_id

    # 3. Regex Pattern for Contract Numbers
    # Example: 04-12030-14  (2 digits - 5 digits - 2 digits)
    # Adjust regex based on actual file naming conventions observed
    contract_pattern = re.compile(r"(\d{2}-\d{5}-\d{2})")

    imported_count = 0
    
    # 4. Check existing files to avoid duplicates
    existing_result = await db.execute(select(FileMeta.path))
    existing_paths = set(existing_result.scalars().all())

    for blob_path in blobs:
        if blob_path in existing_paths:
            continue
        
        # Only process PDFs
        if not blob_path.lower().endswith(".pdf"):
             continue

        filename = os.path.basename(blob_path)
        
        # Try to find Contract Link
        match = contract_pattern.search(filename)
        contract_id = None
        if match:
            c_number = match.group(1)
            if c_number in contract_map:
                contract_id = contract_map[c_number]
                logger.debug("Matched %s -> Contract %s (%s)", filename, c_number, contract_id)

        # Register File
        file_id = uuid.uuid4()
        new_file = FileMeta(
            file_id=file_id,
            path=blob_path,
            content_type="application/pdf",
            created_at=datetime.utcnow()
        )
        if contract_id:
            new_file.contract_id = contract_id
        
        db.add(new_file)
        imported_count += 1
        
        # Trigger Indexing Async
        # We assume file exists in blob since we just listed it
        # Just fire and forget indexing task
        try:
             # We need to commit first so background task can read it? 
             # Or we await indexing here? Scanning might take a while if we await all.
             # Let's commit batch later? No, safer row by row or batch.
             pass 
        except Exception:
             pass

    # Commit all new files
    if imported_count > 0:
        await db.commit()
        
        # Trigger Indexing for all newly added files
        # Re-fetch the files we just added to get their file_ids
        result = await db.execute(
            select(FileMeta).where(
                FileMeta.path.in_([blob_path for blob_path in blobs if blob_path.lower().endswith(".pdf")])
            ).order_by(FileMeta.created_at.desc()).limit(imported_count)
        )
        new_files = result.scalars().all()
        
        indexed_count = 0
        indexing_errors = 0
        
        for file_meta in new_files:
            try:
                await index_pdf_file_async(file_meta.file_id, db, re_index=False)
                indexed_count += 1
                logger.debug("Indexed scanned file: %s", file_meta.file_id)
            except Exception as e:
                indexing_errors += 1
                logger.error(f"Failed to index {file_meta.file_id}: {e}")

    return {
        "message": "Scan complete", 
        "scanned": len(blobs), 
        "newly_imported": imported_count,
        "indexed": indexed_count,
        "indexing_errors": indexing_errors
    }

