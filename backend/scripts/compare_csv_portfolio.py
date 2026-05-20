"""
CSV Portfolio Data Comparison Script

Compares CSV master table data with existing database records.
Generates detailed comparison report showing:
- New records (in CSV but not in DB)
- Updated records (differences between CSV and DB)
- Unchanged records (exact match)
- Orphaned records (in DB but not in CSV)

Usage:
    python3 scripts/compare_csv_portfolio.py [--validate-only]
"""

import sys
import os
import csv
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.db import base  # Import all models via base to resolve relationships
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from sqlalchemy import select

# ============================================================================
# CSV PARSING UTILITIES
# ============================================================================

def parse_status(status_str: str) -> str:
    """Convert Norwegian emoji status to database format."""
    status_map = {
        '🟢 Aktiv': 'active',
        '🔴 UTLØPT': 'terminated',
        '⚫ Opphørt': 'terminated',
        '⚪ Ukjent': 'unknown',
        '❓ Sjekk': 'unknown'
    }
    return status_map.get(status_str.strip(), 'unknown')


def parse_gnr_bnr(gnr_bnr_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse gnr/bnr string like '37/237' into tuple."""
    if not gnr_bnr_str or gnr_bnr_str in ['-', '', 'Ikke oppgitt']:
        return None, None
    try:
        parts = gnr_bnr_str.strip().split('/')
        gnr = int(parts[0]) if parts[0] and parts[0] != '-' else None
        bnr = int(parts[1]) if len(parts) > 1 and parts[1] and parts[1] != '-' else None
        return gnr, bnr
    except (ValueError, IndexError):
        return None, None


def parse_area(area_str: str) -> Optional[float]:
    """Parse area string to float."""
    if not area_str or area_str in ['-', 'Ikke oppgitt', '', 'Flere']:
        return None
    try:
        # Remove spaces, handle comma as decimal separator
        cleaned = area_str.replace(' ', '').replace(',', '.')
        # Handle special cases like "2 rom"
        if 'rom' in cleaned.lower():
            return None
        return float(cleaned)
    except ValueError:
        return None


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string to ISO format."""
    if not date_str or date_str in ['-', 'Ikke oppgitt', '', 'Uleselig']:
        return None
    
    # Handle special formats
    date_str = date_str.strip()
    
    # Try different date formats
    for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y', '%d.%m.%y']:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Handle month/year formats like "Mai 2019", "Nov 2015"
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'mar': '03', 'apr': '04',
        'mai': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'okt': '10', 'nov': '11', 'des': '12'
    }
    for month_name, month_num in month_map.items():
        if month_name in date_str.lower():
            try:
                year = date_str.split()[-1]
                return f"{year}-{month_num}-01"
            except:
                pass
    
    # Handle formats like "05/23"
    if '/' in date_str and len(date_str) <= 5:
        try:
            parts = date_str.split('/')
            if len(parts) == 2:
                return f"20{parts[1]}-{parts[0]}-01"
        except:
            pass
    
    return None


def clean_field(value: str) -> str:
    """Clean field value, replacing empty markers with empty string."""
    if not value or value in ['-', 'Ikke oppgitt', '']:
        return ''
    return value.strip()


def extract_contract_metadata(row: Dict[str, str]) -> Dict[str, Any]:
    """Extract and transform contract metadata from CSV row."""
    gnr, bnr = parse_gnr_bnr(row.get('Gnr/Bnr', ''))
    
    return {
        'csv_row_id': row.get('#', ''),
        'region': clean_field(row.get('Region')),
        'filename': clean_field(row.get('Filnavn (Kilde)')),
        'contract_number': clean_field(row.get('Kontraktnr')),
        'category': clean_field(row.get('Kategori')),
        'address': clean_field(row.get('Adresse')),
        'property_type': clean_field(row.get('Type Lokale')),
        'area_sqm': parse_area(row.get('Areal (m²)', '')),
        'gnr': gnr,
        'bnr': bnr,
        'status': parse_status(row.get('Status (01.01.26)', '')),
        'start_date': parse_date(row.get('Startdato', '')),
        'end_date': parse_date(row.get('Sluttdato', '')),
        'duration': clean_field(row.get('Varighet')),
        'termination_clause': clean_field(row.get('Oppsigelse / Klausuler')),
        'option_extension': clean_field(row.get('Opsjon / Forlengelse')),
        'parking': clean_field(row.get('Parkering / Garasje')),
        'facilities': clean_field(row.get('Fasiliteter / Teknisk / Ute')),
        'signed_date': parse_date(row.get('Signert Dato', '')),
        'created_date': parse_date(row.get('Opprettet Dato', ''))
    }


def load_csv_data(csv_path: str) -> List[Dict[str, Any]]:
    """Load and parse CSV data."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        records = [extract_contract_metadata(row) for row in reader]
    return records


# ============================================================================
# MATCHING UTILITIES
# ============================================================================

def normalize_address(address: str) -> str:
    """Normalize address for matching (lowercase, remove extra spaces)."""
    if not address:
        return ""
    return " ".join(address.lower().strip().split())


def address_similarity(addr1: str, addr2: str) -> float:
    """Calculate similarity score between two addresses."""
    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_match(
    csv_rec: Dict[str, Any],
    db_contracts: List[Any],
    db_properties: Dict[str, Any],
    db_units: Dict[str, Any]
) -> Optional[Tuple[Any, str]]:
    """
    Find matching database record for CSV record.
    Returns (contract, match_type) or None.
    
    Match strategies:
    1. Contract number exact match
    2. Address + gnr/bnr exact match
    3. Address fuzzy match (>0.9 similarity)
    """
    for contract in db_contracts:
        # Strategy 1: Contract number match
        if csv_rec.get('contract_number'):
            external_data = contract.external_data or {}
            db_contract_num = str(external_data.get('contract_number', ''))
            if db_contract_num == csv_rec['contract_number']:
                return (contract, 'contract_number')
        
        # Strategy 2 & 3: Address-based matching
        if contract.unit_id and csv_rec.get('address'):
            unit = db_units.get(str(contract.unit_id))
            if unit and unit.property_id:
                prop = db_properties.get(str(unit.property_id))
                if prop:
                    # Exact gnr/bnr match
                    if csv_rec.get('gnr') and csv_rec.get('bnr'):
                        if (prop.gnr == csv_rec['gnr'] and 
                            prop.bnr == csv_rec['bnr']):
                            return (contract, 'gnr_bnr')
                    
                    # Address fuzzy match
                    if prop.address:
                        similarity = address_similarity(csv_rec['address'], prop.address)
                        if similarity > 0.9:
                            return (contract, f'address_fuzzy_{similarity:.2f}')
    
    return None


# ============================================================================
# DATABASE QUERIES
# ============================================================================

async def fetch_database_data() -> Tuple[List[Any], Dict[str, Any], Dict[str, Any]]:
    """Fetch all contracts, properties, and units from database."""
    async with SessionLocal() as session:
        # Fetch contracts (without joinedload to avoid Party relationship issues)
        stmt = select(Contract)
        result = await session.execute(stmt)
        contracts = result.scalars().all()
        
        # Fetch all properties
        prop_stmt = select(Property)
        prop_result = await session.execute(prop_stmt)
        properties = {str(p.property_id): p for p in prop_result.scalars().all()}
        
        # Fetch all units
        unit_stmt = select(Unit)
        unit_result = await session.execute(unit_stmt)
        units = {str(u.unit_id): u for u in unit_result.scalars().all()}
        
        return contracts, properties, units


# ============================================================================
# COMPARISON & REPORTING
# ============================================================================

def generate_comparison_report(
    csv_records: List[Dict[str, Any]],
    db_contracts: List[Any],
    db_properties: Dict[str, Any],
    db_units: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate detailed comparison report."""
    report = {
        'generated_at': datetime.now().isoformat(),
        'csv_count': len(csv_records),
        'db_count': len(db_contracts),
        'statistics': {
            'new_in_csv': 0,
            'matched': 0,
            'not_in_csv': 0
        },
        'matches': [],
        'new_records': [],
        'unmatched_db_records': []
    }
    
    matched_contract_ids = set()
    
    # Process CSV records
    for csv_rec in csv_records:
        match_result = find_match(csv_rec, db_contracts, db_properties, db_units)
        
        if match_result:
            contract, match_type = match_result
            report['statistics']['matched'] += 1
            matched_contract_ids.add(str(contract.contract_id))
            
            # Collect differences
            differences = []
            
            # Compare status
            if csv_rec['status'] != contract.status:
                differences.append({
                    'field': 'status',
                    'csv_value': csv_rec['status'],
                    'db_value': contract.status
                })
            
            # Compare external_data fields
            external_data = contract.external_data or {}
            for field in ['region', 'filename', 'category', 'parking', 'facilities']:
                csv_val = csv_rec.get(field, '')
                db_val = external_data.get(field, '')
                if csv_val and csv_val != db_val:
                    differences.append({
                        'field': f'external_data.{field}',
                        'csv_value': csv_val,
                        'db_value': db_val
                    })
            
            # Compare gnr/bnr if unit exists
            if contract.unit_id:
                unit = db_units.get(str(contract.unit_id))
                if unit and unit.property_id:
                    prop = db_properties.get(str(unit.property_id))
                    if prop:
                        if csv_rec.get('gnr') and csv_rec['gnr'] != prop.gnr:
                            differences.append({
                                'field': 'property.gnr',
                                'csv_value': csv_rec['gnr'],
                                'db_value': prop.gnr
                            })
                        if csv_rec.get('bnr') and csv_rec['bnr'] != prop.bnr:
                            differences.append({
                                'field': 'property.bnr',
                                'csv_value': csv_rec['bnr'],
                                'db_value': prop.bnr
                            })
            
            report['matches'].append({
                'csv_row_id': csv_rec['csv_row_id'],
                'contract_id': str(contract.contract_id),
                'match_type': match_type,
                'address': csv_rec.get('address'),
                'contract_number': csv_rec.get('contract_number'),
                'differences': differences,
                'has_differences': len(differences) > 0
            })
        else:
            # No match found - new record
            report['statistics']['new_in_csv'] += 1
            report['new_records'].append({
                'csv_row_id': csv_rec['csv_row_id'],
                'address': csv_rec.get('address'),
                'contract_number': csv_rec.get('contract_number'),
                'region': csv_rec.get('region'),
                'status': csv_rec.get('status'),
                'data': csv_rec
            })
    
    # Find unmatched DB records
    for contract in db_contracts:
        if str(contract.contract_id) not in matched_contract_ids:
            report['statistics']['not_in_csv'] += 1
            
            # Get address from property
            address = None
            if contract.unit_id:
                unit = db_units.get(str(contract.unit_id))
                if unit and unit.property_id:
                    prop = db_properties.get(str(unit.property_id))
                    if prop:
                        address = prop.address
            
            report['unmatched_db_records'].append({
                'contract_id': str(contract.contract_id),
                'address': address,
                'status': contract.status,
                'external_data': contract.external_data or {}
            })
    
    return report


def generate_markdown_report(report: Dict[str, Any], output_path: str):
    """Generate human-readable markdown report."""
    lines = [
        "# CSV Portfolio Comparison Report",
        f"\n**Generated:** {report['generated_at']}\n",
        "## Summary Statistics\n",
        f"- **CSV Records:** {report['csv_count']}",
        f"- **Database Contracts:** {report['db_count']}",
        f"- **Matched:** {report['statistics']['matched']}",
        f"- **New in CSV:** {report['statistics']['new_in_csv']}",
        f"- **Not in CSV (DB only):** {report['statistics']['not_in_csv']}\n",
        "## Matched Records\n",
    ]
    
    # Group by whether they have differences
    with_diffs = [m for m in report['matches'] if m['has_differences']]
    without_diffs = [m for m in report['matches'] if not m['has_differences']]
    
    lines.append(f"### Records with Differences ({len(with_diffs)})\n")
    for match in with_diffs[:20]:  # Limit to first 20
        lines.append(f"#### CSV Row #{match['csv_row_id']} - {match['address']}")
        lines.append(f"- **Match Type:** {match['match_type']}")
        lines.append(f"- **Contract ID:** `{match['contract_id']}`")
        lines.append("- **Differences:**")
        for diff in match['differences']:
            lines.append(f"  - `{diff['field']}`: CSV=`{diff['csv_value']}` | DB=`{diff['db_value']}`")
        lines.append("")
    
    if len(with_diffs) > 20:
        lines.append(f"*...and {len(with_diffs) - 20} more records with differences*\n")
    
    lines.append(f"\n### Records Without Differences ({len(without_diffs)})\n")
    lines.append("These records match perfectly between CSV and database.\n")
    
    lines.append(f"\n## New Records in CSV ({len(report['new_records'])})\n")
    for new_rec in report['new_records'][:20]:
        lines.append(f"- **Row #{new_rec['csv_row_id']}**: {new_rec['address']} (Contract: {new_rec['contract_number'] or 'N/A'})")
    
    if len(report['new_records']) > 20:
        lines.append(f"\n*...and {len(report['new_records']) - 20} more new records*\n")
    
    lines.append(f"\n## Unmatched Database Records ({len(report['unmatched_db_records'])})\n")
    for db_rec in report['unmatched_db_records'][:20]:
        lines.append(f"- **Contract {db_rec['contract_id']}**: {db_rec['address'] or 'No address'}")
    
    if len(report['unmatched_db_records']) > 20:
        lines.append(f"\n*...and {len(report['unmatched_db_records']) - 20} more unmatched DB records*\n")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ============================================================================
# MAIN
# ============================================================================

async def main(validate_only: bool = False):
    """Main execution function."""
    print("=" * 80)
    print("CSV PORTFOLIO DATA COMPARISON")
    print("=" * 80)
    
    # Load CSV data
    csv_path = Path(__file__).parent.parent / 'data' / 'csv_portfolio_data.csv'
    print(f"\n1. Loading CSV data from {csv_path}...")
    csv_records = load_csv_data(str(csv_path))
    print(f"   ✓ Loaded {len(csv_records)} CSV records")
    
    # Statistics
    regions = {}
    statuses = {}
    for rec in csv_records:
        if rec['region']:
            regions[rec['region']] = regions.get(rec['region'], 0) + 1
        if rec['status']:
            statuses[rec['status']] = statuses.get(rec['status'], 0) + 1
    
    print(f"\n   Regions: {regions}")
    print(f"   Statuses: {statuses}")
    
    if validate_only:
        print("\n✓ Validation complete. Use without --validate-only to compare with database.")
        return
    
    # Fetch database data
    print("\n2. Fetching database data...")
    contracts, properties, units = await fetch_database_data()
    print(f"   ✓ Loaded {len(contracts)} contracts")
    print(f"   ✓ Loaded {len(properties)} properties")
    print(f"   ✓ Loaded {len(units)} units")
    
    # Generate comparison report
    print("\n3. Comparing CSV with database...")
    report = generate_comparison_report(csv_records, contracts, properties, units)
    
    # Save reports
    output_dir = Path(__file__).parent.parent / 'data'
    json_path = output_dir / 'csv_comparison_report.json'
    md_path = output_dir / 'csv_comparison_report.md'
    
    print(f"\n4. Generating reports...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Saved JSON report: {json_path}")
    
    generate_markdown_report(report, str(md_path))
    print(f"   ✓ Saved Markdown report: {md_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"CSV Records:              {report['csv_count']}")
    print(f"Database Contracts:       {report['db_count']}")
    print(f"Matched:                  {report['statistics']['matched']}")
    print(f"New in CSV:               {report['statistics']['new_in_csv']}")
    print(f"Not in CSV (DB only):     {report['statistics']['not_in_csv']}")
    print("=" * 80)
    
    # Highlight records with differences
    with_diffs = [m for m in report['matches'] if m['has_differences']]
    print(f"\n⚠️  {len(with_diffs)} matched records have differences that need review")
    print(f"\nNext steps:")
    print(f"1. Review the comparison report: {md_path}")
    print(f"2. If everything looks good, run: python3 scripts/update_from_csv.py")


if __name__ == '__main__':
    validate_only = '--validate-only' in sys.argv
    asyncio.run(main(validate_only))
