"""
FDV Document Intelligence Service
– Tekstuttrekk (pypdf, pytesseract)
– Embedding via OpenAI
– Semantisk søk med pgvector cosine similarity
"""
from __future__ import annotations

import io
import logging
from typing import List, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings import generate_embeddings, generate_query_embedding

logger = logging.getLogger(__name__)


async def extract_text(file_bytes: bytes, filename: str) -> tuple[str, int]:
    """
    Returner (extracted_text, page_count).
    Prøver pypdf for PDF, pytesseract for bilder.
    Fallback: returner ("", 0) om begge feiler.
    """
    fname_lower = filename.lower()

    # ── PDF ──────────────────────────────────────────────────────────────────
    if fname_lower.endswith(".pdf"):
        try:
            import pypdf  # type: ignore

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages = reader.pages
            page_count = len(pages)
            parts: list[str] = []
            for page in pages:
                try:
                    parts.append(page.extract_text() or "")
                except Exception:
                    parts.append("")
            extracted = "\n".join(parts).strip()
            return extracted, page_count
        except Exception as e:
            logger.debug("pypdf extraction failed for %s: %s", filename, e)

    # ── Bilde (OCR) ───────────────────────────────────────────────────────────
    image_exts = (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp")
    if any(fname_lower.endswith(ext) for ext in image_exts):
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore

            img = Image.open(io.BytesIO(file_bytes))
            extracted = pytesseract.image_to_string(img).strip()
            return extracted, 1
        except Exception as e:
            logger.debug("pytesseract extraction failed for %s: %s", filename, e)

    return "", 0


async def process_document(db: AsyncSession, document_id: str) -> bool:
    """
    1. Hent FdvDocument fra DB
    2. Sett extraction_status = 'processing'
    3. Last ned fil (file_path eller external_url)
    4. extract_text()
    5. generate_embeddings([text]) fra embeddings.py
    6. Lagre extracted_text, embedding, page_count, extraction_status = 'done'
    7. Returner True ved suksess, sett 'failed' ved feil
    """
    from app.domains.fdv.models.compliance import FdvDocument
    import uuid

    try:
        doc_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        doc = await db.get(FdvDocument, doc_uuid)
        if not doc:
            logger.debug("process_document: document %s not found", document_id)
            return False

        # Mark as processing
        doc.extraction_status = "processing"
        await db.commit()

        # Resolve file source
        file_bytes: Optional[bytes] = None
        filename = doc.title or "document"

        if doc.file_path:
            # Internal path – try reading from filesystem
            try:
                import aiofiles  # type: ignore

                async with aiofiles.open(doc.file_path, "rb") as f:
                    file_bytes = await f.read()
                filename = doc.file_path.split("/")[-1]
            except Exception as e:
                logger.debug("Could not read file_path %s: %s", doc.file_path, e)

        if file_bytes is None and doc.external_url:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(doc.external_url)
                    resp.raise_for_status()
                    file_bytes = resp.content
                filename = doc.external_url.split("/")[-1].split("?")[0] or filename
            except Exception as e:
                logger.debug("Could not download external_url %s: %s", doc.external_url, e)

        if file_bytes is None:
            logger.debug("process_document: no file content available for %s", document_id)
            doc.extraction_status = "failed"
            await db.commit()
            return False

        # Extract text
        extracted_text, page_count = await extract_text(file_bytes, filename)

        # Generate embedding (only if we have text)
        embedding: Optional[list] = None
        if extracted_text:
            try:
                embeddings = generate_embeddings([extracted_text])
                if embeddings:
                    embedding = embeddings[0]
            except Exception as e:
                logger.debug("Embedding generation failed for %s: %s", document_id, e)

        # Persist
        doc.extracted_text = extracted_text or None
        doc.page_count = page_count or None
        doc.embedding = embedding
        doc.extraction_status = "done"
        await db.commit()
        logger.debug("process_document: done for %s (pages=%s, has_embedding=%s)", document_id, page_count, embedding is not None)
        return True

    except Exception as e:
        logger.error("process_document failed for %s: %s", document_id, e)
        try:
            from app.domains.fdv.models.compliance import FdvDocument
            import uuid

            doc_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
            doc = await db.get(FdvDocument, doc_uuid)
            if doc:
                doc.extraction_status = "failed"
                await db.commit()
        except Exception:
            pass
        return False


async def semantic_search(
    db: AsyncSession,
    query: str,
    property_id: Optional[str] = None,
    limit: int = 10,
) -> List[dict]:
    """
    1. generate_query_embedding(query) fra embeddings.py
    2. pgvector cosine similarity søk mot fdv_documents.embedding
    3. Returner liste med document_id, title, document_type, property_id, similarity, excerpt (200 tegn)
    """
    query_embedding = generate_query_embedding(query)
    if not query_embedding:
        logger.debug("semantic_search: no query embedding generated")
        return []

    # Build SQL with optional property filter
    prop_filter = ""
    params: dict = {"query_vec": str(query_embedding), "limit": limit}

    if property_id:
        prop_filter = "AND d.property_id = :property_id"
        params["property_id"] = property_id

    sql = text(f"""
        SELECT
            d.document_id,
            d.title,
            d.document_type,
            d.property_id,
            1 - (d.embedding <=> :query_vec::vector) AS similarity,
            LEFT(d.extracted_text, 200) AS excerpt
        FROM fdv_documents d
        WHERE d.embedding IS NOT NULL
          AND d.extraction_status = 'done'
          {prop_filter}
        ORDER BY d.embedding <=> :query_vec::vector
        LIMIT :limit
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.mappings().all()
        return [
            {
                "document_id": str(row["document_id"]),
                "title": row["title"],
                "document_type": row["document_type"],
                "property_id": str(row["property_id"]),
                "similarity": float(row["similarity"]) if row["similarity"] is not None else 0.0,
                "excerpt": row["excerpt"],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error("semantic_search failed: %s", e)
        return []
