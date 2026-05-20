#!/usr/bin/env python3
"""
LangExtract + Docling POC
==========================

Demonstrates integration of Docling (PDF text extraction) with LangExtract
(LLM-based structured extraction with source grounding).

This script:
1. Uses Docling to extract text from a PDF
2. Defines extraction schema for lease contracts
3. Uses LangExtract to extract structured entities with source citations
4. Outputs JSON with precise source references
5. Generates interactive HTML visualization

Cost: ~3-5 øre per 30-page document (Gemini Flash)
"""

import os
import sys
import json
import textwrap
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf_processor import extract_text_from_pdf
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

# Check for langextract
try:
    import langextract as lx
except ImportError:
    logger.error("langextract not installed. Run: pip install langextract")
    sys.exit(1)


def create_lease_extraction_schema() -> tuple[str, List[lx.data.ExampleData]]:
    """
    Define extraction schema and examples for lease contracts.
    
    Returns:
        Tuple of (prompt_description, examples)
    """
    
    # Extraction prompt
    prompt = textwrap.dedent("""
        Extract key information from lease contracts in order of appearance.
        Use exact text for extractions. Do not paraphrase or overlap entities.
        
        Extraction classes:
        - lease_party: Tenant or landlord information (names, organizations)
        - financial_term: Rent amounts, deposits, fees, payment terms
        - date: Contract dates (start date, end date, signing date)
        - duration: Lease period or duration
        - property_detail: Property address, description, area
        - clause: Important contract clauses or terms
        
        Provide meaningful attributes to add context to each extraction.
    """).strip()
    
    # Few-shot examples to guide the model
    examples = [
        lx.data.ExampleData(
            text=textwrap.dedent("""
                LEIEAVTALE
                
                Utleier: Storgata Eiendom AS, org.nr. 123456789
                Leietaker: Kari Nordmann, fødselsår 1985
                
                Leieobjekt: Storgata 12, 0123 Oslo, 2. etasje, 65 kvm
                
                Leieperiode: Fra 01.01.2024 til 31.12.2024 (12 måneder)
                
                Leie: Kr 15.000,- per måned, forfaller den 1. i hver måned.
                Depositum: Kr 45.000,- (3 måneders leie)
            """).strip(),
            extractions=[
                lx.data.Extraction(
                    extraction_class="lease_party",
                    extraction_text="Utleier: Storgata Eiendom AS, org.nr. 123456789",
                    attributes={"role": "landlord", "type": "organization"}
                ),
                lx.data.Extraction(
                    extraction_class="lease_party",
                    extraction_text="Leietaker: Kari Nordmann, fødselsår 1985",
                    attributes={"role": "tenant", "type": "individual"}
                ),
                lx.data.Extraction(
                    extraction_class="property_detail",
                    extraction_text="Leieobjekt: Storgata 12, 0123 Oslo, 2. etasje, 65 kvm",
                    attributes={"type": "address_and_area"}
                ),
                lx.data.Extraction(
                    extraction_class="duration",
                    extraction_text="Fra 01.01.2024 til 31.12.2024 (12 måneder)",
                    attributes={"period": "12 months"}
                ),
                lx.data.Extraction(
                    extraction_class="date",
                    extraction_text="01.01.2024",
                    attributes={"date_type": "start_date"}
                ),
                lx.data.Extraction(
                    extraction_class="date",
                    extraction_text="31.12.2024",
                    attributes={"date_type": "end_date"}
                ),
                lx.data.Extraction(
                    extraction_class="financial_term",
                    extraction_text="Kr 15.000,- per måned",
                    attributes={"type": "monthly_rent", "amount": "15000"}
                ),
                lx.data.Extraction(
                    extraction_class="financial_term",
                    extraction_text="Depositum: Kr 45.000,- (3 måneders leie)",
                    attributes={"type": "deposit", "amount": "45000"}
                ),
            ]
        ),
    ]
    
    return prompt, examples


def extract_with_langextract(
    text: str,
    model_id: str = "gemini-2.0-flash-exp",
    output_dir: Path = None
) -> Dict[str, Any]:
    """
    Extract structured information from text using LangExtract.
    
    Args:
        text: Input text to extract from
        model_id: LLM model to use (default: gemini-2.0-flash-exp)
        output_dir: Directory to save outputs
        
    Returns:
        Dict with extraction results and metadata
    """
    if output_dir is None:
        output_dir = Path.cwd()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting LangExtract with model: {model_id}")
    logger.info(f"Input text length: {len(text)} characters")
    
    # Get extraction schema
    prompt, examples = create_lease_extraction_schema()
    
    # Run extraction
    try:
        result = lx.extract(
            text_or_documents=text,
            prompt_description=prompt,
            examples=examples,
            model_id=model_id,
        )
        
        logger.info(f"Extraction completed successfully")
        
        # Save results to JSONL
        jsonl_path = output_dir / "langextract_output.jsonl"
        lx.io.save_annotated_documents([result], output_name=str(jsonl_path))
        logger.info(f"Saved JSONL output to: {jsonl_path}")
        
        # Generate HTML visualization
        html_content = lx.visualize(str(jsonl_path))
        html_path = output_dir / "langextract_visualization.html"
        
        with open(html_path, "w", encoding="utf-8") as f:
            if hasattr(html_content, 'data'):
                f.write(html_content.data)  # For Jupyter/Colab
            else:
                f.write(html_content)
        
        logger.info(f"Saved HTML visualization to: {html_path}")
        
        # Extract and format results
        extractions = []
        if hasattr(result, 'extractions'):
            for ext in result.extractions:
                extractions.append({
                    'class': ext.extraction_class,
                    'text': ext.extraction_text,
                    'attributes': ext.attributes,
                    'source_location': {
                        'start': getattr(ext, 'start_index', None),
                        'end': getattr(ext, 'end_index', None),
                    }
                })
        
        # Calculate approximate cost (Gemini Flash pricing)
        # Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
        # Rough estimate: 1 token ≈ 0.75 words
        words = len(text.split())
        estimated_input_tokens = int(words * 1.3)
        estimated_output_tokens = len(extractions) * 50  # Rough estimate
        
        input_cost = (estimated_input_tokens / 1_000_000) * 0.075
        output_cost = (estimated_output_tokens / 1_000_000) * 0.30
        total_cost_usd = input_cost + output_cost
        total_cost_nok = total_cost_usd * 10.5  # Approximate USD to NOK
        
        return {
            'extractions': extractions,
            'total_extractions': len(extractions),
            'output_files': {
                'jsonl': str(jsonl_path),
                'html': str(html_path),
            },
            'cost_estimate': {
                'input_tokens': estimated_input_tokens,
                'output_tokens': estimated_output_tokens,
                'total_usd': round(total_cost_usd, 6),
                'total_nok': round(total_cost_nok, 4),
            }
        }
        
    except Exception as e:
        logger.error(f"LangExtract failed: {e}")
        raise


def run_poc(pdf_path: str = None, output_dir: str = None):
    """
    Run the complete POC pipeline.
    
    Args:
        pdf_path: Path to PDF file (if None, uses sample text)
        output_dir: Output directory for results
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "langextract_output"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("LangExtract + Docling POC")
    logger.info("=" * 80)
    
    # Step 1: Extract text from PDF (or use sample)
    if pdf_path:
        logger.info(f"\nStep 1: Extracting text from PDF: {pdf_path}")
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return
        
        extraction_result = extract_text_from_pdf(pdf_path)
        text = extraction_result['text']
        source = extraction_result['source']
        
        logger.info(f"Extracted {len(text)} characters using {source}")
    else:
        logger.info("\nStep 1: Using sample lease contract text")
        text = textwrap.dedent("""
            LEIEAVTALE FOR NÆRINGSLOKALE
            
            Denne leieavtalen er inngått mellom:
            
            UTLEIER: Oslo Sentrum Eiendom AS, org.nr. 987654321
            Adresse: Kongens gate 5, 0153 Oslo
            
            LEIETAKER: Smartcentia AS, org.nr. 123456789
            Adresse: Storgata 12, 0155 Oslo
            
            § 1 LEIEOBJEKT
            Leieobjektet er lokale i 3. etasje i bygningen Storgata 12, 0155 Oslo.
            Bruksareal: 120 kvm (kontorareale)
            Parkeringsplasser: 2 stk i felles parkeringskjeller
            
            § 2 LEIEPERIODE
            Leieforholdet starter 01.03.2024 og løper til 28.02.2027 (3 år).
            Avtalen kan forlenges med 2 år ved skriftlig avtale senest 6 måneder før utløp.
            
            § 3 LEIE OG BETALING
            Årlig leie: Kr 360.000,- ekskl. mva.
            Månedlig leie: Kr 30.000,- ekskl. mva.
            Leien forfaller forskuddsvis den 1. i hver måned.
            
            Depositum: Kr 90.000,- (3 måneders leie)
            Depositumet skal betales senest ved overtakelse.
            
            § 4 FELLESKOSTNADER
            Leietaker betaler andel av felleskostnader beregnet etter BTA.
            Estimert månedlig felleskostnad: Kr 5.000,-
            
            § 5 REGULERING
            Leien reguleres årlig per 1. januar i henhold til endring i KPI (konsumprisindeks).
            Første regulering skjer 01.01.2025.
            
            § 6 OPPSIGELSE
            Gjensidig oppsigelsesfrist er 6 måneder.
            Oppsigelse skal skje skriftlig.
            
            Oslo, 15.02.2024
            
            _________________________          _________________________
            For Oslo Sentrum Eiendom AS        For Smartcentia AS
            Daglig leder                       Daglig leder
        """).strip()
    
    # Step 2: Run LangExtract
    logger.info("\nStep 2: Running LangExtract for structured extraction")
    
    try:
        result = extract_with_langextract(text, output_dir=output_dir)
        
        # Step 3: Display results
        logger.info("\n" + "=" * 80)
        logger.info("EXTRACTION RESULTS")
        logger.info("=" * 80)
        
        logger.info(f"\nTotal extractions: {result['total_extractions']}")
        
        logger.info("\nExtracted entities:")
        for i, ext in enumerate(result['extractions'], 1):
            logger.info(f"\n{i}. {ext['class'].upper()}")
            logger.info(f"   Text: {ext['text'][:100]}...")
            logger.info(f"   Attributes: {ext['attributes']}")
            if ext['source_location']['start'] is not None:
                logger.info(f"   Location: chars {ext['source_location']['start']}-{ext['source_location']['end']}")
        
        logger.info("\n" + "=" * 80)
        logger.info("COST ANALYSIS")
        logger.info("=" * 80)
        cost = result['cost_estimate']
        logger.info(f"Input tokens: {cost['input_tokens']:,}")
        logger.info(f"Output tokens: {cost['output_tokens']:,}")
        logger.info(f"Total cost: ${cost['total_usd']:.6f} USD (~{cost['total_nok']:.2f} NOK)")
        
        logger.info("\n" + "=" * 80)
        logger.info("OUTPUT FILES")
        logger.info("=" * 80)
        logger.info(f"JSONL: {result['output_files']['jsonl']}")
        logger.info(f"HTML:  {result['output_files']['html']}")
        logger.info("\nOpen the HTML file in a browser to see interactive visualization!")
        
        # Save summary JSON
        summary_path = output_dir / "extraction_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Summary: {summary_path}")
        
        logger.info("\n" + "=" * 80)
        logger.info("POC COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\nPOC failed: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LangExtract + Docling POC")
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to PDF file (optional, uses sample text if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for results (default: backend/langextract_output)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv("GOOGLE_GENAI_API_KEY"):
        logger.error(
            "GOOGLE_GENAI_API_KEY environment variable not set!\n"
            "Get your API key from: https://aistudio.google.com/apikey\n"
            "Then run: export GOOGLE_GENAI_API_KEY='your-key-here'"
        )
        sys.exit(1)
    
    run_poc(pdf_path=args.pdf, output_dir=args.output_dir)
