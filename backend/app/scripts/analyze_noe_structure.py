
import re
import collections

def analyze():
    with open('backend/docs/noe.txt', 'r') as f:
        lines = f.readlines()

    middle_sections = []
    
    # regex to capture:
    # Group 1: Region (Start to ID)
    # Group 2: ID (6 digits)
    # Group 3: Middle (Between ID and Amount)
    # Group 4: Amount (Last token, number with comma/minus)
    
    # Note: Amount is space separated at the end.
    pattern = re.compile(r'^(.*?) (\d{6}) (.*) ((-?[\d]+,[\d]+)|(-?[\d]+))$')
    # Adjusted regex to handle integer amounts too if any (though sample showed commas)
    
    print(f"Total lines: {len(lines)}")
    
    match_count = 0
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Simple split by space to get last token
        parts = line.split(' ')
        amount = parts[-1]
        
        # Re-construct line without amount
        rest = " ".join(parts[:-1])
        
        # Find ID
        # Search for the first 6-digit number match
        id_match = re.search(r' (\d{6}) ', rest)
        if id_match:
            idx = id_match.start()
            end_idx = id_match.end()
            
            region_part = rest[:idx]
            id_part = id_match.group(1)
            middle_part = rest[end_idx:]
            
            middle_sections.append(middle_part)
            match_count += 1
        else:
            # Try to handle the case like 513401 ... 53520
            # It seems the first one is the "main" ID? Or the last one?
            # In line 20: 5 Region ... 513401 ... 53520 ... 
            # If we take the first 6 digit number.
            pass

    print(f"Matched {match_count} lines")
    
    known_categories = [
        "Barnevernsinstitusjoner",
        "Fosterhjemstjenesten",
        "Regionale fellesfunksjoner",
        "Sentre for foreldre og barn",
        "Familieverntjeneste",
        "Omsorgssentre for mindreårige",
        "Statlig regionalt barnevernmyndighet", # Guess
        "Beredskapshjem"
    ]
    
    unmatched_lines = []
    cost_Vendor_chunks = []
    
    for m in middle_sections:
        found = False
        # Sort categories by length desc to match longest first
        for cat in sorted(known_categories, key=len, reverse=True):
            if cat in m:
                # Split by the LAST occurrence of the category
                # Because property name might contain similar words? unlikely.
                parts = m.rpartition(cat)
                # parts[0] = Property
                # parts[1] = Category
                # parts[2] = Cost + Vendor
                cost_Vendor_chunks.append(parts[2].strip())
                found = True
                break
        if not found:
            unmatched_lines.append(m)

    print("\n--- Coverage Report ---")
    print(f"Total Lines: {len(middle_sections)}")
    print(f"Matched: {len(cost_Vendor_chunks)}")
    print(f"Unmatched: {len(unmatched_lines)}")
    
    if unmatched_lines:
        print("\n--- Sample Unmatched ---")
        for u in unmatched_lines[:20]:
            print(u)
            
    print("\n--- Top Cost+Vendor Starts (Potential Cost Types) ---")
    # We look at the first 3 words of the chunk
    starts = []
    for c in cost_Vendor_chunks:
        tokens = c.split()
        if not tokens: continue
        # Take up to 4 tokens
        starts.append(" ".join(tokens[:4]))
        starts.append(" ".join(tokens[:3]))
        starts.append(" ".join(tokens[:2]))
        
    print(collections.Counter(starts).most_common(30))


if __name__ == "__main__":
    analyze()
