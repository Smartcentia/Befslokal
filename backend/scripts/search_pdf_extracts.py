"""
Søk i ekstrahert tekst fra pdf_docs/extracted/ (etter at parse_pdf_folder.py er kjørt).

Kjør fra backend: python scripts/search_pdf_extracts.py "søkeord"
"""
import os
import sys
from pathlib import Path

# Prosjektrot / pdf_docs
_backend = Path(__file__).resolve().parent.parent
PROJECT_ROOT = _backend.parent
PDF_DOCS = Path(os.environ.get("PDF_DOCS", str(PROJECT_ROOT / "pdf_docs")))
EXTRACTED = PDF_DOCS / "extracted"


def main():
    if len(sys.argv) < 2:
        print("Bruk: python scripts/search_pdf_extracts.py \"søkeord\"")
        print("   Søker (case-insensitive) i alle .txt i pdf_docs/extracted/")
        sys.exit(0)

    query = sys.argv[1].strip().lower()
    if not query:
        sys.exit(0)

    if not EXTRACTED.is_dir():
        print(f"❌ Ingen extracted-mappe: {EXTRACTED}")
        print("   Kjør først: python scripts/parse_pdf_folder.py")
        sys.exit(1)

    txts = list(EXTRACTED.glob("*.txt"))
    if not txts:
        print(f"⚠️  Ingen .txt-filer i {EXTRACTED}")
        sys.exit(0)

    hits = []
    for path in sorted(txts):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"   Kunne ikke lese {path.name}: {e}")
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if query in line.lower():
                hits.append((path.name, i, line.strip()))

    if not hits:
        print(f"Ingen treff for «{query}» i {len(txts)} filer.")
        return

    print(f"Treff for «{query}» ({len(hits)} linjer):\n")
    for fname, line_no, line in hits[:50]:
        preview = line[:120] + "..." if len(line) > 120 else line
        print(f"  {fname}:{line_no}  {preview}")
    if len(hits) > 50:
        print(f"  ... og {len(hits) - 50} treff til.")


if __name__ == "__main__":
    main()
