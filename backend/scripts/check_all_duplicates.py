
import os
import glob
from collections import defaultdict

def check_all_duplicates():
    # Pattern to match 01.txt to 12.txt
    files = sorted(glob.glob("docs/*.txt"))
    
    # We only care about the numbered financial files for now, plus maybe check if others are involved
    # logical_files = [f for f in files if os.path.basename(f)[:2].isdigit() and int(os.path.basename(f)[:2]) <= 12]
    # Actually user said "all data", let's check all .txt files in docs that match the pattern
    
    target_files = []
    for f in files:
        basename = os.path.basename(f)
        if basename[0].isdigit() and basename.endswith('.txt'):
             target_files.append(f)
             
    print(f"Checking {len(target_files)} files for cross-contamination: {', '.join([os.path.basename(f) for f in target_files])}")
    print("-" * 50)
    
    line_map = defaultdict(list)
    
    file_line_counts = {}
    
    for file_path in target_files:
        basename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                file_line_counts[basename] = len(lines)
                for idx, line in enumerate(lines):
                    content = line.strip()
                    if not content: continue
                    # Store (filename, line_number)
                    line_map[content].append((basename, idx + 1))
        except Exception as e:
            print(f"Error reading {basename}: {e}")

    # Analyze duplicates
    cross_file_dupes = 0
    internal_dupes = 0
    total_dupe_instances = 0
    
    cross_file_collisions = defaultdict(int) # (fileA, fileB) -> count
    
    for content, occurrences in line_map.items():
        if len(occurrences) > 1:
            total_dupe_instances += 1
            
            files_involved = sorted(list(set([o[0] for o in occurrences])))
            
            # Internal duplicates
            if len(files_involved) == 1:
                internal_dupes += 1
                # print(f"Internal duplicate in {files_involved[0]}: '{content[:50]}...'")
            else:
                cross_file_dupes += 1
                # Record collision pairs
                for i in range(len(files_involved)):
                    for j in range(i+1, len(files_involved)):
                        pair = (files_involved[i], files_involved[j])
                        cross_file_collisions[pair] += 1
                        
                if cross_file_dupes <= 5: # Sample output
                    print(f"CROSS-FILE DUPLICATE FOUND:")
                    print(f"  Content: {content}")
                    print(f"  Found in: {', '.join([f'{o[0]}:{o[1]}' for o in occurrences])}")
                    print("")

    print("-" * 50)
    print("SUMMARY")
    print(f"Total unique line contents: {len(line_map)}")
    print(f"Lines appearing more than once (total): {total_dupe_instances}")
    print(f"Internal duplicates (same file): {internal_dupes}")
    print(f"Cross-file duplicates (different files): {cross_file_dupes}")
    
    if cross_file_collisions:
        print("\nCross-File Collision Matrix:")
        for pair, count in cross_file_collisions.items():
            print(f"  {pair[0]} <-> {pair[1]}: {count} shared lines")
            
            # Heuristic for full subset
            countA = file_line_counts[pair[0]]
            countB = file_line_counts[pair[1]]
            print(f"    (Coverage: {count}/{countA} of {pair[0]}, {count}/{countB} of {pair[1]})")

    # Specific check for 12.txt internal duplicates
    if '12.txt' in file_line_counts:
        with open('docs/12.txt', 'r', encoding='utf-8') as f:
            lines_12 = [l.strip() for l in f.readlines() if l.strip()]
        
        unique_12 = set(lines_12)
        total_12 = len(lines_12)
        dupes_12 = total_12 - len(unique_12)
        print("\nSpecific Check for 12.txt:")
        print(f"  Total lines: {total_12}")
        print(f"  Unique lines: {len(unique_12)}")
        print(f"  Internal duplicates: {dupes_12}")

if __name__ == "__main__":
    check_all_duplicates()
