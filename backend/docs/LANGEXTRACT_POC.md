# LangExtract + Docling POC - Brukerveiledning

## Oversikt

Dette POC-scriptet demonstrerer hvordan man kan kombinere **Docling** (PDF tekstekstraksjon) med **LangExtract** (LLM-basert strukturert ekstraksjon med kildehenvisninger) for å ekstrahere strukturert data fra leieavtaler og andre dokumenter.

## Hva gjør scriptet?

1. **Ekstraher tekst** fra PDF med Docling (eller bruker eksempeltekst)
2. **Definer ekstraksjonsschema** for leieavtaler (leietaker, beløp, datoer, etc.)
3. **Kjør LangExtract** for å ekstrahere strukturert data med LLM
4. **Generer output**:
   - JSON-fil med presise kildehenvisninger
   - Interaktiv HTML-visualisering som viser hva som ble ekstrahert og hvor

## Forutsetninger

### 1. Installer avhengigheter

```bash
cd backend
python3 -m pip install git+https://github.com/google/langextract.git
```

### 2. Skaff Google Gemini API-nøkkel

1. Gå til [Google AI Studio](https://aistudio.google.com/apikey)
2. Opprett en API-nøkkel (gratis tier fungerer fint for testing)
3. Sett miljøvariabel:

```bash
export GOOGLE_GENAI_API_KEY="din-api-nøkkel-her"
```

## Bruk

### Kjør med eksempeltekst (ingen PDF nødvendig)

```bash
cd backend
python3 scripts/langextract_poc.py
```

Dette bruker en innebygd eksempel-leieavtale og viser alle funksjoner.

### Kjør med din egen PDF

```bash
python3 scripts/langextract_poc.py --pdf /path/to/leieavtale.pdf
```

### Spesifiser output-mappe

```bash
python3 scripts/langextract_poc.py --output-dir /path/to/output
```

## Output-filer

Scriptet genererer følgende filer i `backend/langextract_output/`:

1. **`langextract_output.jsonl`** - Strukturerte ekstraksjoner i JSONL-format
2. **`langextract_visualization.html`** - Interaktiv HTML-visualisering (åpne i nettleser!)
3. **`extraction_summary.json`** - Oppsummering med kostnadsanalyse

## Ekstraksjonsschema for leieavtaler

Scriptet er konfigurert til å ekstrahere følgende informasjon:

| Klasse | Beskrivelse | Eksempel |
|--------|-------------|----------|
| `lease_party` | Leietaker eller utleier | "Leietaker: Kari Nordmann" |
| `financial_term` | Leiebeløp, depositum, gebyrer | "Kr 15.000,- per måned" |
| `date` | Datoer (start, slutt, signering) | "01.01.2024" |
| `duration` | Leieperiode | "12 måneder" |
| `property_detail` | Adresse, beskrivelse, areal | "Storgata 12, 65 kvm" |
| `clause` | Viktige kontraktsklausuler | "Oppsigelsesfrist 3 måneder" |

Hver ekstraksjon inkluderer:
- **Eksakt tekst** fra dokumentet
- **Attributter** for kontekst (f.eks. `{"role": "tenant", "type": "individual"}`)
- **Kildeposisjon** (start/slutt i teksten)

## Kostnadsanalyse

### Estimert kostnad per dokument

| Dokumentstørrelse | Modell | Kostnad (NOK) |
|-------------------|--------|---------------|
| 30 sider | Gemini Flash | 3-5 øre |
| 30 sider | Gemini Pro | 50-80 øre |

**Anbefaling:** Bruk `gemini-2.0-flash-exp` (standard) for de fleste dokumenter.

### Eksempel fra kjøring

```
COST ANALYSIS
Input tokens: 2,500
Output tokens: 400
Total cost: $0.000375 USD (~0.04 NOK)
```

## Tilpasning

### Endre ekstraksjonsschema

Rediger `create_lease_extraction_schema()` i `langextract_poc.py`:

```python
# Legg til ny ekstraksjonsklasse
lx.data.Extraction(
    extraction_class="ny_klasse",
    extraction_text="eksakt tekst fra dokumentet",
    attributes={"type": "beskrivelse"}
)
```

### Bruk annen LLM-modell

```python
# I extract_with_langextract()
result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-pro",  # Endre her
)
```

Tilgjengelige modeller:
- `gemini-2.0-flash-exp` (standard, rask og billig)
- `gemini-2.5-pro` (bedre for komplekse dokumenter)
- OpenAI-modeller (krever ekstra konfigurasjon)

## Integrasjon med eksisterende system

### Bruk i produksjon

For å integrere med eksisterende `pdf_processor.py`:

```python
from scripts.langextract_poc import extract_with_langextract
from app.services.pdf_processor import extract_text_from_pdf

# 1. Ekstraher tekst med Docling
result = extract_text_from_pdf("contract.pdf")
text = result['text']

# 2. Ekstraher strukturert data med LangExtract
extractions = extract_with_langextract(text, output_dir=Path("./output"))

# 3. Lagre i database
for ext in extractions['extractions']:
    # Lagre i TextContent eller egen tabell
    save_to_db(ext)
```

### Batch-prosessering

For å prosessere mange dokumenter:

```python
import asyncio
from pathlib import Path

async def process_all_contracts():
    pdf_dir = Path("pdf_docs")
    for pdf_file in pdf_dir.glob("*.pdf"):
        try:
            # Ekstraher og prosesser
            result = extract_text_from_pdf(pdf_file)
            extractions = extract_with_langextract(result['text'])
            
            # Lagre resultater
            save_extractions(pdf_file.stem, extractions)
            
        except Exception as e:
            logger.error(f"Feil ved prosessering av {pdf_file}: {e}")

asyncio.run(process_all_contracts())
```

## Feilsøking

### ImportError: No module named 'langextract'

**Løsning:**
```bash
python3 -m pip install git+https://github.com/google/langextract.git
```

### API Key Error

**Problem:** `GOOGLE_GENAI_API_KEY environment variable not set!`

**Løsning:**
```bash
export GOOGLE_GENAI_API_KEY="your-key-here"
```

### Ingen ekstraksjoner funnet

**Mulige årsaker:**
- Dokumentet har ikke relevant informasjon
- Prompt/eksempler matcher ikke dokumenttypen
- LLM-modellen forstår ikke språket (norsk)

**Løsning:**
- Sjekk at dokumentet inneholder forventet informasjon
- Tilpass eksempler i `create_lease_extraction_schema()`
- Bruk en kraftigere modell (gemini-2.5-pro)

## Neste steg

1. **Test med egne PDF-er** - Kjør scriptet med leieavtaler fra BEFS
2. **Evaluer nøyaktighet** - Sjekk HTML-visualiseringen for å validere ekstraksjoner
3. **Tilpass schema** - Legg til flere ekstraksjonsklasser etter behov
4. **Integrer i produksjon** - Vurder å legge til i eksisterende PDF-pipeline

## Referanser

- [LangExtract GitHub](https://github.com/google/langextract)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Dokumentasjon](https://ai.google.dev/gemini-api/docs)
- [BEFS Docling Dokumentasjon](../docs/PDF_PROSESSERING_DOCLING.md)
