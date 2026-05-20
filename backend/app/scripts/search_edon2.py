import os

def search_edon2():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    file_path = os.path.join(BACKEND_DIR, 'e-don2.txt')
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    targets = ["1217", "Lamo", "2335", "3608", "3522"]
    print(f"Searching {file_path} for {targets}...")
    
    with open(file_path, 'r', encoding='latin-1') as f:
        lines = f.readlines()
    
    print(f"Total lines in file: {len(lines)}")
    found_count = 0
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(t.lower() in line_lower for t in targets):
            print(f"MATCH on line {i}: {line.strip()[:100]}...")
            found_count += 1
            
    if found_count == 0:
        print("NO TARGETS FOUND IN FILE.")

if __name__ == "__main__":
    search_edon2()
