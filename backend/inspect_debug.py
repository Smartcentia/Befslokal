import re

def inspect_file():
    with open("bufdir_source.html", "r") as f:
        content = f.read()
    
    target = 'institutions'
    # Use re to find "institutions" to handle escaped quotes
    matches = [m.start() for m in re.finditer(r'institutions', content)]
    for idx in matches:
        print(f"Found 'institutions' at index {idx}")
        print("Context:")
        print(content[idx-100:idx+300])
        print("-" * 20)

if __name__ == "__main__":
    inspect_file()
