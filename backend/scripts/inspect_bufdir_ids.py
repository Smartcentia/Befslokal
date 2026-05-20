import re

URL = "https://www.bufdir.no/barnevern/finn-institusjon/"

def inspect_ids():
    with open("bufdir_source.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # Just find all "id":... matches and print context
    matches = list(re.finditer(r'\\?"id\\?":\d+', html))
    print(f"Found {len(matches)} matches.")
    
    for i in range(min(10, len(matches))):
        m = matches[i]
        start = max(0, m.start() - 50)
        end = min(len(html), m.end() + 200)
        print(f"Match {i}: ...{html[start:end]}...")
        print("-" * 20)

if __name__ == "__main__":
    inspect_ids()
