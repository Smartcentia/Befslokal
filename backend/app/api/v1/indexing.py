from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.search.indexer import batch_index_all_files

router = APIRouter()

@router.post("/batch-index")
async def trigger_batch_indexing(
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger batch indexing of all PDF files in the database.
    This is typically used for:
    - Initial setup
    - Re-indexing after index schema changes
    - Recovery after indexing failures
    """
    try:
        result = await batch_index_all_files(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch indexing failed: {str(e)}"
        )

@router.get("/indexing-status")
async def get_indexing_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Check indexing status - how many files are in DB vs indexed.
    """
    from app.models.file_meta import FileMeta
    from sqlalchemy import select, func
    
    # Count total PDF files
    result = await db.execute(
        select(func.count()).select_from(FileMeta).where(
            FileMeta.content_type == "application/pdf"
        )
    )
    total_pdfs = result.scalar()
    
    # Return total files for now

    return {
        "total_pdf_files": total_pdfs,
        "message": "Indexing status - check logs for detailed results"
    }
