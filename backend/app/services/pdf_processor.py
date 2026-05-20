"""PDF text extraction and chunking service using Docling with PyPDF fallback."""
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import os
import pypdf
from app.services.infrastructure.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


def extract_with_docling(pdf_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Ekstraher tekst og strukturert innhold fra PDF ved bruk av Docling.
    Returnerer strukturert data inkludert tekst, tabeller, metadata, etc.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF-fil ikke funnet: {pdf_path}")

    try:
        from docling.document_converter import DocumentConverter
    except ImportError as e:
        raise ImportError(
            "Docling krever 'docling' pakke. Installer med: pip install docling"
        ) from e

    logger.info(f"Starter Docling-analyse av {pdf_path.name}...")
    
    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        
        # Extract text content
        full_text = result.document.export_to_markdown()
        
        # Extract tables if enabled
        tables = []
        if settings.DOCLING_EXTRACT_TABLES:
            # Docling stores tables in the document structure
            # We'll extract them from the document object
            for element in result.document.body:
                if hasattr(element, 'table') and element.table:
                    tables.append({
                        'data': element.table.to_dict() if hasattr(element.table, 'to_dict') else str(element.table),
                        'caption': getattr(element, 'caption', None)
                    })
        
        # Extract metadata
        metadata = {
            'num_pages': getattr(result.document, 'num_pages', 0),
            'title': getattr(result.document, 'title', None),
            'author': getattr(result.document, 'author', None),
            'creation_date': getattr(result.document, 'creation_date', None),
        }
        
        logger.info(
            f"Docling-analyse fullført. Ekstraherte {len(full_text)} tegn, "
            f"{len(tables)} tabeller fra {pdf_path.name}"
        )
        
        return {
            'text': full_text,
            'tables': tables,
            'metadata': metadata,
            'source': 'docling'
        }
    
    except Exception as e:
        logger.error(f"Feil ved Docling-analyse: {e}")
        raise


def extract_text_from_pdf_pypdf(pdf_path: Union[str, Path]) -> str:
    """
    Ekstraher tekst fra PDF-fil ved bruk av PyPDF (fallback method).
    Dette bruker PyPDF for å ekstrahere tekst fra PDF-filer.
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF-fil ikke funnet: {pdf_path}")
    
    try:
        logger.info(f"Starter PyPDF tekstanalyse av {pdf_path.name}...")
        text_parts = []
        with open(pdf_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text() or "")
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"PyPDF-analyse fullført. Ekstraherte {len(full_text)} tegn.")
        return full_text

    except Exception as e:
        logger.error(f"Feil ved PyPDF-analyse: {e}")
        raise


def extract_text_from_pdf_ocr(
    pdf_path: Union[str, Path],
    lang: str = "nor+eng",
) -> str:
    """
    Ekstraher tekst fra PDF ved OCR (Tesseract). For skannede PDF-er uten tekstlag.
    Krever: tesseract + poppler (macOS: brew install tesseract poppler), og pip: pdf2image, pytesseract.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF-fil ikke funnet: {pdf_path}")

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as e:
        raise ImportError(
            "OCR krever pdf2image og pytesseract. Installer med: pip install pdf2image pytesseract. "
            "Og installer tesseract + poppler (macOS: brew install tesseract poppler)."
        ) from e

    logger.info(f"Starter OCR av {pdf_path.name} (Tesseract, lang={lang})...")
    images = convert_from_path(str(pdf_path), dpi=200)
    text_parts = []
    for i, img in enumerate(images):
        page_text = pytesseract.image_to_string(img, lang=lang)
        text_parts.append(page_text or "")
    full_text = "\n\n".join(text_parts)
    logger.info(f"OCR fullført. Ekstraherte {len(full_text)} tegn fra {len(images)} sider.")
    return full_text


def extract_text_from_pdf(pdf_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Ekstraher tekst fra PDF-fil. Bruker Docling hvis aktivert, ellers PyPDF.
    Returnerer dict med text, tables (hvis tilgjengelig), metadata, og source.
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF-fil ikke funnet: {pdf_path}")
    
    # Try Docling first if enabled
    if settings.USE_DOCLING:
        try:
            return extract_with_docling(pdf_path)
        except Exception as e:
            logger.warning(f"Docling feilet: {e}")
            if settings.DOCLING_FALLBACK_TO_PYPDF:
                logger.info("Faller tilbake til PyPDF...")
            else:
                raise
    
    # Fallback to PyPDF
    try:
        text = extract_text_from_pdf_pypdf(pdf_path)
        return {
            'text': text,
            'tables': [],
            'metadata': {},
            'source': 'pypdf'
        }
    except Exception as e:
        logger.error(f"Både Docling og PyPDF feilet for {pdf_path.name}")
        raise


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[str]:
    """
    Del tekst opp i chunks av passende størrelse.
    """
    # Use config default if not provided
    chunk_size = chunk_size or 1000
    chunk_overlap = chunk_overlap or 100
    
    if not text or len(text.strip()) == 0:
        return []
    
    # Enkel chunking-strategi: del på linjeskift først, deretter på størrelse
    chunks = []
    
    # Del først på paragrafer (dobbel linjeskift)
    paragraphs = text.split("\n\n")
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Hvis paragraph er for stor alene, del den opp
        if len(paragraph) > chunk_size:
            # Hvis vi har akkumulert tekst, legg den til først
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Del lange paragrafer på setninger eller størrelse
            words = paragraph.split()
            current_words = []
            current_length = 0
            
            for word in words:
                word_length = len(word) + 1  # +1 for space
                if current_length + word_length > chunk_size and current_words:
                    chunks.append(" ".join(current_words))
                    # Overlap: behold siste ordene
                    overlap_words = current_words[-chunk_overlap // 10:] if chunk_overlap else []
                    current_words = overlap_words
                    current_length = sum(len(w) + 1 for w in current_words)
                
                current_words.append(word)
                current_length += word_length
            
            if current_words:
                chunks.append(" ".join(current_words))
        
        else:
            # Hvis vi kan legge til paragraph i nåværende chunk
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:  # +2 for "\n\n"
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            else:
                # Legg til nåværende chunk og start ny
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
    
    # Legg til siste chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    # Hvis ingen chunks ble opprettet, legg til hele teksten
    if not chunks and text:
        chunks = [text]
    
    logger.debug(f"Opprettet {len(chunks)} chunks fra tekst ({len(text)} tegn)")
    return chunks


def process_pdf(
    pdf_path: Union[str, Path],
    contract_id: str,
    file_id: str
) -> List[Dict[str, Any]]:
    """
    Prosesser PDF-fil: ekstraher tekst og del opp i chunks.
    Returnerer liste av chunks med metadata.
    """
    try:
        # Ekstraher tekst (med Docling eller PyPDF)
        extraction_result = extract_text_from_pdf(pdf_path)
        text = extraction_result['text']
        tables = extraction_result.get('tables', [])
        metadata = extraction_result.get('metadata', {})
        source = extraction_result.get('source', 'unknown')
        
        # Del opp i chunks
        chunks = chunk_text(text)
        
        # Opprett metadata for hver chunk
        result = []
        for idx, chunk_content in enumerate(chunks):
            chunk_data = {
                "text": chunk_content,
                "chunk_index": idx,
                "contract_id": contract_id,
                "file_id": file_id,
                "total_chunks": len(chunks),
                "source": source,
            }
            
            # Add tables to first chunk if any
            if idx == 0 and tables:
                chunk_data["tables"] = tables
            
            # Add metadata to first chunk
            if idx == 0 and metadata:
                chunk_data["pdf_metadata"] = metadata
            
            result.append(chunk_data)
        
        logger.info(
            f"Prosessert PDF: {Path(pdf_path).name} -> "
            f"{len(chunks)} chunks, {len(tables)} tabeller "
            f"(contract_id={contract_id}, source={source})"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Feil ved prosessering av PDF {pdf_path}: {e}")
        raise
