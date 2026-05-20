import os

def check_files():
    # Use same logic as import script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    
    files = ['e-don2.txt', 'e-dom.txt']
    targets = ["1217", "Lamo", "2335", "3608", "3522"]
    
    for filename in files:
        path = os.path.join(BACKEND_DIR, filename)
        print(f"\n--- Checking {filename} ---")
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
            
        try:
            with open(path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
            
            print(f"Rows: {len(lines)}")
            if lines:
                print(f"Header: {lines[0].strip()}")
                print(f"First data row: {lines[1].strip() if len(lines) > 1 else 'N/A'}")
            
            found = []
            for line in lines:
                if any(t.lower() in line.lower() for t in targets):
                    found.append(line.strip())
            
            if found:
                print(f"FOUND TARGETS ({len(found)}):")
                for f in found[:5]:
                    print(f"  - {f[:120]}...")
            else:
                print("TARGETS NOT FOUND.")
        except Exception as e:
            print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    check_files()
