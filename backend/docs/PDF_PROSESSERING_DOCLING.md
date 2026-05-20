# PDF-prosessering med Docling - Teknisk dokumentasjon

## Oversikt

BEFS bruker **Docling** som primær PDF-parser med PyPDF som fallback. Docling gir avansert dokumentforståelse inkludert tabell-ekstraksjon, layout-analyse og metadata-ekstraksjon.

## Arkitektur

### Komponenter

1. **pdf_processor.py** - Hovedtjeneste for PDF-prosessering
2. **indexer.py** - Indeksering av PDF-innhold til database
3. **parse_pdf_folder.py** - Batch-script for masseprosessering
4. **config.py** - Konfigurasjon av Docling-funksjoner

### Dataflyt

```
PDF-fil → pdf_processor.py → Docling/PyPDF → Tekst + Tabeller + Metadata
                                                        ↓
                                              chunk_text() → Chunks
                                                        ↓
                                              indexer.py → TextContent (DB)
                                                        ↓
                                              Søkbar via KI-Kollega
```

## Konfigurasjon

Alle innstillinger finnes i `backend/app/core/config.py`:

```python
# PDF Processing with Docling
USE_DOCLING: bool = True  # Enable Docling for advanced PDF parsing
DOCLING_FALLBACK_TO_PYPDF: bool = True  # Fallback to PyPDF if Docling fails
DOCLING_EXTRACT_TABLES: bool = True  # Extract tables as structured data
DOCLING_EXTRACT_IMAGES: bool = False  # Extract images (resource-intensive)
DOCLING_OCR_ENABLED: bool = True  # OCR for scanned documents
```

### Miljøvariabler

Sett i `.env` for å overstyre standardverdier:

```bash
USE_DOCLING=true
DOCLING_FALLBACK_TO_PYPDF=true
DOCLING_EXTRACT_TABLES=true
DOCLING_EXTRACT_IMAGES=false
DOCLING_OCR_ENABLED=true
```

## API-bruk

### Prosessere en PDF

```python
from app.services.pdf_processor import process_pdf

# Prosesser PDF og få chunks med metadata
chunks = process_pdf(
    pdf_path="/path/to/document.pdf",
    contract_id="contract-uuid",
    file_id="file-uuid"
)

# Resultat: Liste av chunks med tekst, tabeller og metadata
for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}: {len(chunk['text'])} tegn")
    if 'tables' in chunk:
        print(f"  Tabeller: {len(chunk['tables'])}")
    if 'pdf_metadata' in chunk:
        print(f"  Metadata: {chunk['pdf_metadata']}")
```

### Ekstrahere tekst direkte

```python
from app.services.pdf_processor import extract_text_from_pdf

# Ekstraher med Docling (eller PyPDF som fallback)
result = extract_text_from_pdf("/path/to/document.pdf")

print(f"Kilde: {result['source']}")  # 'docling' eller 'pypdf'
print(f"Tekst: {result['text'][:100]}...")
print(f"Tabeller: {len(result['tables'])}")
print(f"Metadata: {result['metadata']}")
```

## Batch-prosessering

### Script-bruk

Prosesser alle PDF-er i en mappe:

```bash
cd backend

# Standard: Bruk Docling
python3 scripts/parse_pdf_folder.py

# Med OCR fallback for skannede dokumenter
python3 scripts/parse_pdf_folder.py --ocr-fallback

# Kun OCR (for skannede dokumenter)
python3 scripts/parse_pdf_folder.py --ocr
```

### Output

Scriptet oppretter:
- `pdf_docs/extracted/*.txt` - Ekstrahert tekst per PDF
- `pdf_docs/extracted/manifest.json` - Metadata om prosesseringen

Eksempel manifest-entry:

```json
{
  "source": "kontrakt_storgata12.pdf",
  "extracted": "kontrakt_storgata12.txt",
  "chars": 15234,
  "chunks": 12,
  "source_note": "docling",
  "tables_count": 3,
  "pdf_metadata": {
    "title": "Leieavtale Storgata 12",
    "author": "Bufetat",
    "num_pages": 5
  }
}
```

## Database-lagring

### TextContent-modell

PDF-chunks lagres i `text_content`-tabellen med utvidet metadata:

```python
{
    "content": "Chunk-tekst...",
    "embedding": [0.1, 0.2, ...],  # Vektor for semantisk søk
    "source_file": "file-uuid",
    "source_type": "pdf",
    "chunk_index": 0,
    "additional_metadata": {
        "contract_id": "contract-uuid",
        "file_id": "file-uuid",
        "source": "docling",
        "tables": [
            {
                "data": {"headers": ["A", "B"], "rows": [["1", "2"]]},
                "caption": "Prisliste"
            }
        ],
        "pdf_metadata": {
            "title": "Leieavtale",
            "num_pages": 5
        }
    }
}
```

### Indeksering

```python
from app.services.search.indexer import index_pdf_file_async

# Indekser en PDF-fil
await index_pdf_file_async(
    file_id=file_uuid,
    db=async_session,
    re_index=True  # Slett eksisterende og re-indekser
)
```

## Feilhåndtering

### Fallback-strategi

1. **Docling feiler** → Prøv PyPDF (hvis `DOCLING_FALLBACK_TO_PYPDF=true`)
2. **PyPDF feiler** → Kast exception
3. **Ingen tekst funnet** → Prøv OCR (hvis `--ocr-fallback` i script)

### Logging

All prosessering logges til `backend.log`:

```
INFO - Starter Docling-analyse av kontrakt.pdf...
INFO - Docling-analyse fullført. Ekstraherte 15234 tegn, 3 tabeller
INFO - Prosessert PDF: kontrakt.pdf -> 12 chunks, 3 tabeller (source=docling)
```

Ved feil:

```
WARNING - Docling feilet: ImportError: No module named 'docling'
INFO - Faller tilbake til PyPDF...
INFO - PyPDF-analyse fullført. Ekstraherte 14892 tegn.
```

## Ytelse

### Benchmarks

Typiske prosesseringstider (MacBook Pro M1):

| PDF-type | Sider | Docling | PyPDF | Tabeller |
|----------|-------|---------|-------|----------|
| Enkel tekst | 5 | 2.3s | 0.4s | 0 |
| Med tabeller | 10 | 4.1s | 0.8s | 5 |
| Skannet (OCR) | 3 | 8.7s | N/A | 0 |

### Optimalisering

For bedre ytelse:

```bash
# Deaktiver tabell-ekstraksjon
DOCLING_EXTRACT_TABLES=false

# Deaktiver bilde-ekstraksjon
DOCLING_EXTRACT_IMAGES=false

# Bruk kun PyPDF (raskest, men ingen tabeller)
USE_DOCLING=false
```

## Feilsøking

### Docling importfeil

**Problem:** `ImportError: No module named 'docling'`

**Løsning:**
```bash
cd backend
pip install -r requirements.txt
```

### Modellnedlasting feiler

**Problem:** Docling kan ikke laste ned ML-modeller

**Løsning:**
- Sjekk internettforbindelse
- Sjekk diskplass (~500MB for modeller)
- Sjekk brannmur/proxy-innstillinger

### Ingen tabeller ekstrahert

**Problem:** PDF har tabeller, men ingen blir funnet

**Mulige årsaker:**
- `DOCLING_EXTRACT_TABLES=false` i config
- Tabellene er bilder (krever `DOCLING_EXTRACT_IMAGES=true`)
- PDF-en har kompleks layout

**Løsning:**
```bash
# Aktiver tabell-ekstraksjon
DOCLING_EXTRACT_TABLES=true

# For tabeller i bilder
DOCLING_EXTRACT_IMAGES=true
```

### OCR fungerer ikke

**Problem:** Skannede PDF-er gir tom tekst

**Løsning:**

1. Installer systemavhengigheter:
```bash
# macOS
brew install tesseract poppler

# Linux
sudo apt-get install tesseract-ocr poppler-utils
```

2. Installer Python-pakker:
```bash
pip install pdf2image pytesseract
```

3. Kjør med OCR:
```bash
python3 scripts/parse_pdf_folder.py --ocr-fallback
```

## Testing

### Kjør unit tester

```bash
cd backend
python3 -m pytest tests/test_pdf_processor_docling.py -v
```

### Test med ekte PDF

```bash
# Legg PDF i pdf_docs/
cp /path/to/test.pdf ../pdf_docs/

# Kjør parsing
python3 scripts/parse_pdf_folder.py

# Sjekk resultat
cat ../pdf_docs/extracted/manifest.json | jq '.[] | select(.source == "test.pdf")'
```

## Vedlikehold

### Oppdatere Docling

```bash
cd backend
pip install --upgrade docling
```

### Rydde cache

Docling lagrer modeller i `~/.cache/docling/`:

```bash
# Slett cache (modeller lastes ned på nytt)
rm -rf ~/.cache/docling/
```

### Re-indeksere alle PDF-er

```bash
# Fra backend
python3 -c "
from app.db.session import SessionLocal
from app.services.search.indexer import batch_index_all_files
import asyncio

async def main():
    async with SessionLocal() as db:
        result = await batch_index_all_files(db)
        print(f'Indeksert: {result[\"indexed\"]}, Feilet: {result[\"failed\"]}')

asyncio.run(main())
"
```

## Sikkerhet

### Filvalidering

PDF-filer valideres før prosessering:

- Maks filstørrelse: 50MB (konfigurerbart)
- Tillatte MIME-typer: `application/pdf`
- Virus-scanning (hvis aktivert)

### Datahåndtering

- PDF-innhold lagres kryptert i database
- Midlertidige filer slettes etter prosessering
- Ingen data sendes til eksterne tjenester (Docling kjører lokalt)

## Referanser

- [Docling GitHub](https://github.com/docling-project/docling)
- [Docling Dokumentasjon](https://docling-project.github.io/docling/)
- [PyPDF Dokumentasjon](https://pypdf.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
