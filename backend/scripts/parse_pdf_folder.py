"""
Parser alle PDF-filer i pdf_docs-mappen og lagrer ekstrahert tekst i pdf_docs/extracted/.

Kjør fra backend: python3 scripts/parse_pdf_folder.py
  --ocr          Bruk OCR (Tesseract) på alle PDF-er (for skannede dokumenter).
  --ocr-fallback Bruk OCR bare når PyPDF ikke finner tekst (anbefalt for blandet mappe).

Krever for OCR: tesseract + poppler (macOS: brew install tesseract poppler), og pip: pdf2image pytesseract.
"""
import argparse
import os
import sys
import json
from pathlib import Path

# Sørg for at backend er på path slik at app.* fungerer
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.services.pdf_processor import extract_text_from_pdf, extract_text_from_pdf_ocr, chunk_text

# Standard: pdf_docs i prosjektrot (søster til backend)
PROJECT_ROOT = _backend.parent
DEFAULT_PDF_DOCS = PROJECT_ROOT / "pdf_docs"
EXTRACTED_DIR = "extracted"


def main():
    parser = argparse.ArgumentParser(description="Parser PDF-er i pdf_docs og lagrer tekst i extracted/")
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Bruk Tesseract OCR på alle PDF-er (for skannede dokumenter).",
    )
    parser.add_argument(
        "--ocr-fallback",
        action="store_true",
        help="Bruk OCR bare når PyPDF ikke finner tekst (anbefalt for blandet mappe).",
    )
    args = parser.parse_args()

    pdf_docs = Path(os.environ.get("PDF_DOCS", str(DEFAULT_PDF_DOCS)))
    if not pdf_docs.is_dir():
        print(f"❌ Mappen finnes ikke: {pdf_docs}")
        print("   Opprett den og legg inn PDF-filer, eller sett PDF_DOCS=/path/til/mappe")
        sys.exit(1)

    out_dir = pdf_docs / EXTRACTED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_docs.glob("**/*.pdf"))
    if not pdfs:
        print(f"⚠️  Ingen PDF-filer funnet i {pdf_docs}")
        sys.exit(0)

    use_ocr_all = args.ocr
    use_ocr_fallback = args.ocr_fallback
    if use_ocr_all:
        print("📄 Modus: OCR (Tesseract) på alle PDF-er")
    elif use_ocr_fallback:
        print("📄 Modus: PyPDF, deretter OCR ved lite/ingen tekst")
    else:
        print("📄 Modus: kun PyPDF (tekst-PDF-er)")
    print(f"   Fant {len(pdfs)} PDF-er i {pdf_docs}\n")
    manifest = []

    for i, pdf_path in enumerate(pdfs, 1):
        rel = pdf_path.relative_to(pdf_docs)
        print(f"   [{i}/{len(pdfs)}] {rel} ...")

        text = ""
        source_note = "pypdf"

        if use_ocr_all:
            try:
                text = extract_text_from_pdf_ocr(pdf_path)
                source_note = "ocr"
            except Exception as e:
                print(f"      ❌ OCR feilet: {e}")
                manifest.append({"source": str(rel), "error": str(e), "chars": 0, "chunks": 0})
                continue
        else:
            try:
                extraction_result = extract_text_from_pdf(pdf_path)
                text = extraction_result['text']
                source_note = extraction_result.get('source', 'unknown')
                tables = extraction_result.get('tables', [])
                pdf_metadata = extraction_result.get('metadata', {})
            except Exception as e:
                print(f"      ❌ Feil: {e}")
                manifest.append({"source": str(rel), "error": str(e), "chars": 0, "chunks": 0})
                continue

            if not text.strip() and use_ocr_fallback:
                try:
                    text = extract_text_from_pdf_ocr(pdf_path)
                    source_note = "ocr (fallback)"
                    tables = []
                    pdf_metadata = {}
                    print("      🔄 Lite tekst fra primær metode – brukte OCR")
                except Exception as e:
                    print(f"      ⚠️  OCR fallback feilet: {e} – lagrer primært resultat")

        out_name = pdf_path.stem + ".txt"
        out_path = out_dir / out_name
        out_path.write_text(text, encoding="utf-8")

        if not text.strip():
            print("      ⚠️  Kun whitespace/ingen lesbar tekst – lagret likevel i .txt")
            manifest.append({
                "source": str(rel),
                "extracted": out_name,
                "chars": len(text),
                "chunks": 0,
                "note": "lite innhold",
            })
        else:
            chunks = chunk_text(text)
            manifest_entry = {
                "source": str(rel),
                "extracted": out_name,
                "chars": len(text),
                "chunks": len(chunks),
                "source_note": source_note,
            }
            
            # Add table count if tables were extracted
            if tables:
                manifest_entry["tables_count"] = len(tables)
            
            # Add PDF metadata if available
            if pdf_metadata:
                manifest_entry["pdf_metadata"] = pdf_metadata
            
            manifest.append(manifest_entry)
            
            table_info = f", {len(tables)} tabeller" if tables else ""
            print(f"      ✅ {len(text)} tegn, {len(chunks)} chunks{table_info} → {out_name} ({source_note})")

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Ferdig. Manifest: {manifest_path}")
    print("   Søk: cd backend && python3 scripts/search_pdf_extracts.py \"søkeord\"")


if __name__ == "__main__":
    main()
