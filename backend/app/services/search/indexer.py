"""PDF indexing service - combines PDF processing, embeddings, and Vector DB storage."""
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.core.config import settings
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func

from app.services.pdf_processor import process_pdf
from app.services.text_processor import process_text_content
from app.services.embeddings import generate_embeddings
from app.services.vectordb import add_documents, delete_documents, get_collection_info
from app.services.storage import get_storage
from app.services.infrastructure.logger import get_logger
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
# Internal Dependencies
from app.models.file_meta import FileMeta
from app.models.text_content import TextContent

logger = get_logger(__name__)


# Sync wrapper removed. Use index_pdf_file_async. 

# Async Wrapper / Rewrite for AsyncSession
async def index_contract_files(db: AsyncSession, contract_ids: List[UUID] = None):
    """
    Indekser filer knyttet til kontrakter.
    Hvis contract_ids er None, indekser alle PDF-filer knyttet til kontrakter.
    """
    logger.info("Starting contract file indexing...")
    
    # Select files that are PDFs and linked to a contract
    stmt = select(FileMeta).where(
        FileMeta.content_type == "application/pdf",
        FileMeta.contract_id.isnot(None)
    )
    
    if contract_ids:
        stmt = stmt.where(FileMeta.contract_id.in_(contract_ids))
        
    result = await db.execute(stmt)
    files = result.scalars().all()
    
    if not files:
        logger.info("No contract files found to index.")
        return
        
    for file_meta in files:
        try:
            await index_pdf_file_async(file_meta.file_id, db, re_index=True)
            logger.info(f"Indexed contract file: {file_meta.file_id}")
        except Exception as e:
            logger.error(f"Failed to index contract file {file_meta.file_id}: {e}")

async def batch_index_all_files(db: AsyncSession):
    """
    Re-indekser alle filer i systemet.
    """
    logger.info("Starting batch indexing of all files...")
    
    # 1. Fetch all PDF files from DB
    result = await db.execute(
        select(FileMeta).where(FileMeta.content_type == "application/pdf")
    )
    files = result.scalars().all()
    
    if not files:
        logger.warning("No PDF files found in database to index")
        return {
            "status": "completed",
            "total_files": 0,
            "indexed": 0,
            "failed": 0,
            "results": []
        }
    
    logger.info(f"Found {len(files)} PDF files to index")
    
    # 2. Index each file
    indexed_count = 0
    failed_count = 0
    results = []
    
    for file_meta in files:
        try:
            logger.info(f"Indexing file {file_meta.file_id}: {file_meta.path}")
            result = await index_pdf_file_async(
                file_id=file_meta.file_id,
                db=db,
                re_index=True  # Re-index to ensure fresh data
            )
            indexed_count += 1
            results.append({
                "file_id": str(file_meta.file_id),
                "status": "success",
                "result": result
            })
            logger.info(f"Successfully indexed {file_meta.file_id}")
        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            logger.error(f"Failed to index {file_meta.file_id}: {error_msg}")
            results.append({
                "file_id": str(file_meta.file_id),
                "status": "failed",
                "error": error_msg
            })
    
    summary = {
        "status": "completed",
        "total_files": len(files),
        "indexed": indexed_count,
        "failed": failed_count,
        "results": results
    }
    
    logger.info(f"Batch indexing complete: {indexed_count} indexed, {failed_count} failed")
    return summary

async def index_pdf_file_async(
    file_id: UUID,
    db: AsyncSession,
    re_index: bool = False
) -> Dict[str, Any]:
    
    result = await db.execute(select(FileMeta).where(FileMeta.file_id == file_id))
    file_meta = result.scalar_one_or_none()
    
    if not file_meta:
        raise ValueError(f"FileMeta ikke funnet for file_id: {file_id}")
    
    # Hent PDF-fil fra storage
    storage = get_storage()
    
    try:
        # Note: storage.get_file is blocking (sync).
        pdf_content = storage.get_file(file_meta.path)
        
        # Skriv til midlertidig fil for prosessering
        temp_pdf_path = Path(f"/tmp/{file_id}.pdf")
        temp_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        temp_pdf_path.write_bytes(pdf_content)
        
        try:
            # Prosesser PDF (ekstraher tekst og chunk)
            chunks_data = process_pdf(
                pdf_path=temp_pdf_path,
                contract_id=str(file_meta.contract_id),
                file_id=str(file_id)
            )
            
            if not chunks_data:
                return {
                    "file_id": str(file_id),
                    "status": "skipped",
                    "reason": "Ingen tekst funnet i PDF",
                    "chunks_indexed": 0
                }
            
            # Slett eksisterende indeks hvis re-indexing
            if re_index:
                # Delete from Postgres TextContent table
                await db.execute(
                    text("DELETE FROM text_content WHERE source_file = :fid"),
                    {"fid": str(file_id)}
                )
                logger.info(f"Deleted existing chunks for file_id: {file_id}")
            
            # Generer embeddings for alle chunks
            texts = [chunk["text"] for chunk in chunks_data]
            embeddings = generate_embeddings(texts)
            
            # Lagre i Postgres TextContent
            for i, chunk in enumerate(chunks_data):
                # Build metadata dict with all available information
                chunk_metadata = {
                    "contract_id": chunk["contract_id"],
                    "file_id": chunk["file_id"],
                    "tags": file_meta.tags,
                    "source": chunk.get("source", "unknown"),
                }
                
                # Add tables if present (typically in first chunk)
                if "tables" in chunk:
                    chunk_metadata["tables"] = chunk["tables"]
                
                # Add PDF metadata if present (typically in first chunk)
                if "pdf_metadata" in chunk:
                    chunk_metadata["pdf_metadata"] = chunk["pdf_metadata"]
                
                new_chunk = TextContent(
                    content=chunk["text"],
                    embedding=embeddings[i], # Assumes pgvector column support
                    search_vector=func.to_tsvector('norwegian', chunk["text"]),
                    source_file=str(file_id),
                    source_type="pdf",
                    category="contract", # Or derive from file_meta
                    chunk_index=chunk["chunk_index"],
                    additional_metadata=chunk_metadata,
                    contract_id=file_meta.contract_id
                )
                db.add(new_chunk)
            
            await db.commit()
            
            logger.info(
                f"Indeksert PDF til Postgres: file_id={file_id}, "
                f"chunks={len(chunks_data)}"
            )
            
            return {
                "file_id": str(file_id),
                "contract_id": str(file_meta.contract_id),
                "status": "success",
                "chunks_indexed": len(chunks_data)
            }
        
        finally:
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
    
    except Exception as e:
        logger.error(f"Feil ved indeksering av PDF file_id={file_id}: {e}")
        await db.rollback()
        raise


def index_api_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Indekser structured API data to Postgres.
    NOTE: Currently stubbed as it requires AsyncSession context which this sync generic function lacks.
    Ideally, this should be an async function called within a route handler.
    """
    return {"status": "skipped_legacy_sync_method", "reason": "Use async generic indexer instead"}
