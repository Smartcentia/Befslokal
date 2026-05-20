
import json
import os

def parse_totalny():
    input_file = "/Users/frank/Documents/BEFS_CLEAN/backend/docs/totalny.txt"
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    try:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not lines:
        print("Empty file")
        return

    headers = lines[0].strip().split('\t')
    print(f"HEADERS: {json.dumps(headers, ensure_ascii=False)}")
    
    # Print first row of data to see values
    if len(lines) > 1:
        first_row = lines[1].strip().split('\t')
        print(f"DATA_ROW_1: {json.dumps(first_row, ensure_ascii=False)}")

if __name__ == "__main__":
    parse_totalny()
