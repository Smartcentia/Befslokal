
import csv

filename = '/Users/frank/BEFS3/KNOWME/backend/docs/Eiendom.csv'

with open(filename, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    
    # Identify column indices
    try:
        idx_kontrakt = header.index("Kontraktsleie ved oppstart (per år)")
        idx_gyldig = header.index("Kontaktsleie ved oppstart (gyldig kontrakt)")
        idx_kpi = header.index("KPI-justert kontraktsleie til okt 2025")
        idx_navn = header.index("Avtalenavn")
    except ValueError as e:
        print(f"Error finding column: {e}")
        print("Header:", header)
        exit()

    unique_values = {}
    match_rows = []

    for row in reader:
        if len(row) < max(idx_kontrakt, idx_gyldig, idx_kpi, idx_navn):
            continue
            
        val_kontrakt = row[idx_kontrakt].strip()
        val_gyldig = row[idx_gyldig].strip()
        val_kpi = row[idx_kpi].strip()
        
        # Collect distinct values to understand the format (e.g. "0" vs "0,-")
        if val_kontrakt not in unique_values:
            unique_values[val_kontrakt] = 0
        unique_values[val_kontrakt] += 1
        
        # Also print lines that look like 0
        if val_kontrakt in ['0', '0,-', '0.0'] or val_gyldig in ['0', '0,-'] or val_kpi in ['0', '0,-']:
             match_rows.append((row[idx_navn], val_kontrakt, val_gyldig, val_kpi))

    print("\nUnique values in 'Kontraktsleie ved oppstart (per år)' (showing first 50):")
    for val, count in list(unique_values.items())[:50]:
        print(f"'{val}': {count}")
    
    print("\nMatches for 0:")
    if match_rows:
        for m in match_rows:
             print(f"{m[0]:<50} | {m[1]:<15} | {m[2]:<15} | {m[3]:<15}")
    else:
        print("No exact '0' matches found.")
