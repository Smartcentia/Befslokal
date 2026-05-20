import asyncio
import sys
import os
import re
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.services.tools.contract_tools import search_contracts

QUERY_FILE = "/Users/frank/.gemini/antigravity/brain/19e678ad-9a23-4fbe-9060-f8f8a3a94d74/contract_test_queries.md"
REPORT_FILE = "/Users/frank/.gemini/antigravity/brain/19e678ad-9a23-4fbe-9060-f8f8a3a94d74/test_execution_report.md"

def extract_queries(file_path):
    queries = []
    with open(file_path, "r") as f:
        for line in f:
            # Match lines starting with "1. ", "50. ", etc.
            match = re.match(r"^\d+\.\s+(.+)", line.strip())
            if match:
                queries.append(match.group(1))
    return queries

async def run_full_suite():
    print(f"Reading queries from {QUERY_FILE}...")
    queries = extract_queries(QUERY_FILE)
    print(f"Found {len(queries)} queries.")
    
    report_lines = [
        "# KI Kollega Test Execution Report",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total Queries**: {len(queries)}",
        "",
        "## Genererte Svar",
        ""
    ]
    
    success_count = 0
    
    for i, q in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Executing: {q}")
        output_snippet = "ERROR"
        status = "❌ Failed"
        
        try:
            result = await search_contracts(q)
            if "Ingen kontrakter funnet" in result and len(result) < 200:
                status = "⚠️ No Results"
                output_snippet = result.strip()
            else:
                status = "✅ Success"
                success_count += 1
                # Format snippet nicely: remove newlines, take first 150 chars
                output_snippet = result.replace("\n", " ").strip()[:150] + "..."
                
        except Exception as e:
            output_snippet = f"Exception: {str(e)}"
            
        # Add to report
        report_lines.append(f"### Q{i}: {q}")
        report_lines.append(f"**Status**: {status}")
        report_lines.append(f"> {output_snippet}")
        report_lines.append("")
        
    # Add summary at top (by inserting after header)
    summary_line = f"**Success Rate**: {success_count}/{len(queries)} ({(success_count/len(queries))*100:.1f}%)"
    report_lines.insert(3, summary_line)
    
    print(f"Writing report to {REPORT_FILE}...")
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(report_lines))
        
    print("Done!")

if __name__ == "__main__":
    asyncio.run(run_full_suite())
