import sys
from pathlib import Path

# Add project root to path to allow importing backend modules
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from backend.app.services.glossary_service import run_glossary_scan

def main():
    result = run_glossary_scan()
    print(f"Scan Status: {result['status']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print(f"Terms Loaded: {result['terms_count']}")
        print(f"Matches Found: {result['matches_count']}")
        print(f"Report Saved: {result['output_file']}")

if __name__ == "__main__":
    main()
