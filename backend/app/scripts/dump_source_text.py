import asyncio
import sys
import os
import re

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select, or_
from app.db.session import SessionLocal
from app.models.text_content import TextContent
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def dump_source_text():
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "alt.md")
    output_path = os.path.abspath(output_path)
    
    async with SessionLocal() as db:
        print("Scanning text content for parking verification dump...\n")
        
        keywords = ["parkering", "garasje", "lading", "p-plass", "ladestasjon", "elbil", "biloppstilling"]
        
        stmt = select(TextContent)
        conditions = [TextContent.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = stmt.where(or_(*conditions))
        
        result = await db.execute(stmt)
        rows = result.scalars().all()
        
        output_lines = ["# Kildedump: Parkering\n\nDette dokumentet inneholder råtekst fra dokumenter hvor nøkkelordene *parkering, garasje, lading, p-plass, elbil* forekommer.\n"]
        
        for text_node in rows:
            content = text_node.content
            if not content:
                continue

            matches = []
            content_lower = content.lower()
            
            # Simple check if any keyword is present
            if not any(kw in content_lower for kw in keywords):
                continue
                
            # Resolve Address/Source
            source_name = "Ukjent kilde"
            
            # Try DB links
            if text_node.contract_id:
                 contract = await db.get(Contract, text_node.contract_id)
                 if contract and contract.unit_id:
                     unit = await db.get(Unit, contract.unit_id)
                     if unit and unit.property_id:
                         prop = await db.get(Property, unit.property_id)
                         if prop:
                             source_name = f"{prop.address}, {prop.city}"
            
            # Fallback to filename
            filename = text_node.source_file or text_node.source_index_id or "N/A"
            if source_name == "Ukjent kilde" and "/" in str(filename):
                parts = str(filename).split("/")
                if len(parts) > 1:
                     source_name = parts[-2] # Folder name often contains address
            
            # Extract content with keywords
            context_blocks = []
            
            # Find all keyword positions
            positions = []
            for kw in keywords:
                for m in re.finditer(kw, content_lower):
                    positions.append((m.start(), m.end()))
            
            positions.sort()
            
            # Merge overlapping or close positions
            merged_ranges = []
            if positions:
                current_start, current_end = positions[0]
                # Expand window (Generous 500 chars)
                current_start = max(0, current_start - 500)
                current_end = min(len(content), current_end + 500)
                
                for i in range(1, len(positions)):
                    next_start, next_end = positions[i]
                    next_start_expanded = max(0, next_start - 500)
                    next_end_expanded = min(len(content), next_end + 500)
                    
                    if next_start_expanded <= current_end: # Overlap or close
                        current_end = max(current_end, next_end_expanded)
                    else:
                        merged_ranges.append((current_start, current_end))
                        current_start = next_start_expanded
                        current_end = next_end_expanded
                merged_ranges.append((current_start, current_end))
            
            for start, end in merged_ranges:
                chunk = content[start:end].strip()
                # Simple markdown escaping
                chunk = chunk.replace("`", "'")
                context_blocks.append(f"> ...{chunk}...")

            if context_blocks:
                output_lines.append(f"## {source_name}")
                output_lines.append(f"**Fil:** `{filename}`\n")
                output_lines.append("\n\n".join(context_blocks))
                output_lines.append("\n---\n")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
            
        print(f"Dump complete. Wrote {len(output_lines)} lines to {output_path}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dump_source_text())
