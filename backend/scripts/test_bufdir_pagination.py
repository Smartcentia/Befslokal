import subprocess
import re

URL = "https://www.bufdir.no/barnevern/finn-institusjon/"

def fetch(params=""):
    url = f"{URL}{params}"
    print(f"Fetching {url}...")
    res = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    return res.stdout

def extract_ids(html):
    return re.findall(r'\\?"id\\?":(\d+)', html)

def main():
    html_1 = fetch("")
    ids_1 = set(extract_ids(html_1))
    print(f"Page 1: Found {len(ids_1)} IDs.")
    
    # Try page 2
    html_2 = fetch("?page=2")
    ids_2 = set(extract_ids(html_2))
    print(f"Page 2: Found {len(ids_2)} IDs.")
    
    # Compare
    new_ids = ids_2 - ids_1
    print(f"New IDs in Page 2: {len(new_ids)}")
    if new_ids:
        print(f"Sample new IDs: {list(new_ids)[:5]}")
    else:
        print("Page 2 has same IDs (Pagination failed).")

if __name__ == "__main__":
    main()
