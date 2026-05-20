"""
Geocode properties missing coordinates using Kartverket/Geonorge API.

This script:
1. Fetches all properties without coordinates
2. Geocodes each address using KartverketClient
3. Updates latitude, longitude, and PostGIS geometry
4. Extracts postal codes from addresses
5. Handles rate limiting and errors gracefully
"""
import asyncio
import re
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.services.external.api_clients.kartverket_client import KartverketClient

# Import all models to ensure SQLAlchemy relationships are properly configured
import app.domains.core.models.user
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.domains.hms.models.checklist
import app.models.ai_tool
import app.models.file_meta



class GeocodingStats:
    """Track geocoding statistics"""
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.skipped = 0
        self.synthetic = 0
        self.failed_addresses: List[Dict[str, str]] = []
        self.start_time = datetime.now()
    
    def print_summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "="*60)
        print("GEOCODING SUMMARY")
        print("="*60)
        print(f"Total properties processed: {self.total}")
        print(f"✅ Successfully geocoded: {self.success} ({self.success/self.total*100:.1f}%)")
        print(f"❌ Failed to geocode: {self.failed} ({self.failed/self.total*100:.1f}%)")
        print(f"⏭️  Skipped (synthetic): {self.skipped}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📊 Rate: {self.total/duration:.1f} properties/second")
        
        if self.failed_addresses:
            print(f"\n❌ Failed Addresses ({len(self.failed_addresses)}):")
            for item in self.failed_addresses[:10]:
                print(f"  - {item['name']}: {item['address']}")
            if len(self.failed_addresses) > 10:
                print(f"  ... and {len(self.failed_addresses) - 10} more")


def extract_postal_code(address: str) -> Optional[str]:
    """
    Extract Norwegian postal code (4 digits) from address string.
    
    Examples:
        "Strandveien 123, 0250 Oslo" -> "0250"
        "Besøksadresse Sandbrekkvegen 27, 5231 Paradis" -> "5231"
    """
    if not address:
        return None
    
    # Norwegian postal code: 4 digits
    match = re.search(r'\b(\d{4})\b', address)
    return match.group(1) if match else None


def is_synthetic_address(address: str) -> bool:
    """
    Check if address is synthetic/placeholder.
    
    Synthetic patterns:
    - "Syntetisk: ..."
    - "$34" (invalid)
    - "ikke oppmålt"
    """
    if not address:
        return False
    
    synthetic_patterns = [
        r'^Syntetisk:',
        r'^\$\d+$',
        r'ikke oppmålt',
        r'^-$',
        r'^\s*$'
    ]
    
    for pattern in synthetic_patterns:
        if re.search(pattern, address, re.IGNORECASE):
            return True
    
    return False


def clean_address(address: str, city: Optional[str] = None) -> str:
    """
    Clean and normalize address for geocoding.
    
    Handles:
    - Multi-line addresses (takes first line with "Besøksadresse")
    - Removes "Besøksadresse" / "Postadresse" prefixes
    
    Note: Does NOT add city name, as Kartverket API works better without it.
    
    Examples:
        "Besøksadresse Sandbrekkvegen 27, 5231 Paradis \\n Postadresse..." 
        -> "Sandbrekkvegen 27, 5231 Paradis"
        
        "Østmarkveien 26 D/E"
        -> "Østmarkveien 26 D/E"
    """
    if not address:
        return address
    
    # Take first line if multi-line
    if '\\n' in address:
        lines = address.split('\\n')
        # Prefer "Besøksadresse" over "Postadresse"
        for line in lines:
            if 'Besøksadresse' in line or 'besøksadresse' in line:
                address = line
                break
        else:
            address = lines[0]
    
    # Remove prefixes
    address = re.sub(r'^(Besøksadresse|Postadresse|Adresse)[\s:]+', '', address, flags=re.IGNORECASE)
    
    # Trim whitespace
    address = address.strip()
    
    return address




async def geocode_properties(
    dry_run: bool = True,
    limit: Optional[int] = None,
    batch_size: int = 50,
    rate_limit_ms: int = 100
):
    """
    Geocode properties missing coordinates.
    
    Args:
        dry_run: If True, don't commit changes to database
        limit: Maximum number of properties to process (for testing)
        batch_size: Number of properties to process before committing
        rate_limit_ms: Milliseconds to wait between API calls
    """
    stats = GeocodingStats()
    kartverket = KartverketClient()
    
    async with SessionLocal() as db:
        # Fetch properties without coordinates
        stmt = select(Property).where(
            (Property.latitude == None) | (Property.longitude == None)
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        stats.total = len(properties)
        
        print(f"\n{'='*60}")
        print(f"GEOCODING PROPERTIES")
        print(f"{'='*60}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Properties to process: {stats.total}")
        print(f"Batch size: {batch_size}")
        print(f"Rate limit: {rate_limit_ms}ms between requests")
        print(f"{'='*60}\n")
        
        if stats.total == 0:
            print("✅ No properties need geocoding!")
            return
        
        # Process in batches
        for i, prop in enumerate(properties, 1):
            print(f"[{i}/{stats.total}] Processing: {prop.name or prop.address}")
            
            if not prop.address:
                print("  ⏭️  Skipping - missing address")
                stats.skipped += 1
                stats.failed_addresses.append({
                    "name": prop.name or "[No name]",
                    "address": "[Missing address]"
                })
                continue

            # Check if address is synthetic
            if is_synthetic_address(prop.address):
                print(f"  ⏭️  Skipping synthetic address: {prop.address}")
                stats.skipped += 1
                stats.synthetic += 1
                continue
            
            # Clean address for better geocoding
            cleaned_address = clean_address(prop.address, prop.city)
            print(f"  🔍 Searching: {cleaned_address}")
            
            # Geocode address using structured city/postal filters when available
            try:
                coords = await kartverket.search_address(
                    prop.address,
                    city=prop.city,
                    postal_code=prop.postal_code,
                )

                
                if coords and coords.get('latitude') and coords.get('longitude'):
                    lat = coords['latitude']
                    lon = coords['longitude']
                    
                    # Update property (geom/PostGIS not used in current schema)
                    prop.latitude = lat
                    prop.longitude = lon
                    
                    # Extract and update postal code
                    postal_code = extract_postal_code(prop.address)
                    if postal_code:
                        prop.postal_code = postal_code
                    
                    print(f"  ✅ Geocoded: ({lat:.6f}, {lon:.6f})")
                    if postal_code:
                        print(f"     Postal code: {postal_code}")
                    
                    stats.success += 1
                else:
                    print(f"  ❌ No coordinates found")
                    stats.failed += 1
                    stats.failed_addresses.append({
                        "name": prop.name or "[No name]",
                        "address": prop.address
                    })
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats.failed += 1
                stats.failed_addresses.append({
                    "name": prop.name or "[No name]",
                    "address": prop.address,
                    "error": str(e)
                })
            
            # Rate limiting
            await asyncio.sleep(rate_limit_ms / 1000)
            
            # Commit batch
            if i % batch_size == 0:
                if not dry_run:
                    await db.commit()
                    print(f"\n  💾 Committed batch {i//batch_size}\n")
                else:
                    print(f"\n  🔍 Dry run - would commit batch {i//batch_size}\n")
        
        # Final commit
        if not dry_run:
            await db.commit()
            print(f"\n💾 Final commit completed")
        else:
            print(f"\n🔍 Dry run - no changes committed")
    
    # Print summary
    stats.print_summary()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Geocode properties missing coordinates using Kartverket API"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing changes to database"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of properties to process (for testing)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of properties to process before committing (default: 50)"
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=100,
        help="Milliseconds to wait between API calls (default: 100ms)"
    )
    
    args = parser.parse_args()
    
    await geocode_properties(
        dry_run=args.dry_run,
        limit=args.limit,
        batch_size=args.batch_size,
        rate_limit_ms=args.rate_limit
    )


if __name__ == "__main__":
    asyncio.run(main())
