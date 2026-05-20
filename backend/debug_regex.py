import re
import json

def test_regex():
    with open("debug_bufdir.html", "r") as f:
        content = f.read()
    
    # Try to find the array of institutions
    # Looking for [{"id":..., "regionId":...
    
    # We can try to match the whole array block.
    # It seems to be key "items" or similar not visible in the snippet.
    # But we can find individual items.
    
    # Pattern for ONE item
    pattern = r'\{"id":\d+,"regionId":\d+,.*?"institutionTypes":\[.*?\].*?\}'
    matches = re.findall(pattern, content)
    print(f"Found {len(matches)} matches.")
    
    if matches:
        print("Sample:", matches[0][:100])
        # Validate JSON of one item
        try:
            item = json.loads(matches[0])
            print("Successfully parsed one item.")
        except:
            print("Failed to parse item JSON.")

if __name__ == "__main__":
    test_regex()
