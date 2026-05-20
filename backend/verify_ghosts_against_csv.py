
import csv
import sys
import os

# Define the paths to the CSV files
csv_paths = [
    "/Users/frank/BEFS3/KNOWME/backend/docs/Eiendomsportefølje_ 2025.csv",
    "/Users/frank/BEFS3/KNOWME/backend/data/csv_portfolio_data.csv"
]

ghost_names = [
    "Wenchebo", 
    "Borg", 
    "Skjerven", 
    "Eikelund"
]

def check_csv(file_path):
    print(f"\nChecking file: {file_path}")
    if not os.path.exists(file_path):
        print("File not found.")
        return

    found_ghosts = {}
    
    try:
        with open(file_path, mode='r', encoding='utf-8', errors='replace') as csvfile:
            # Detect dialect or assume semi-colon
            reader = csv.reader(csvfile, delimiter=';')
            headers = next(reader, None)
            
            print(f"Headers found: {headers[:5]} ...")

            for row_idx, row in enumerate(reader):
                row_str = " ".join(row).lower()
                
                for ghost in ghost_names:
                    if ghost.lower() in row_str:
                        if ghost not in found_ghosts:
                            found_ghosts[ghost] = []
                        found_ghosts[ghost].append(row)

        # Report findings
        if not found_ghosts:
            print("No ghost properties found in this file.")
        else:
            for ghost, rows in found_ghosts.items():
                print(f"\nFound '{ghost}' ({len(rows)} matches):")
                for row in rows:
                    # Print relevant columns if possible, otherwise print whole row nicely
                    # In Eiendomsportefølje_ 2025.csv, col 0 is Lokalisering, col 1 Avtalenavn, col 11 Adresselinje 1, col 15 Areal
                    if "Eiendomsportefølje" in file_path:
                        try:
                            name = row[1]
                            address = row[11]
                            area = row[15]
                            print(f"  - Name: {name}, Address: {address}, Area: {area} m2")
                        except IndexError:
                            print(f"  - Raw Row: {row[:5]}...")
                    else:
                        print(f"  - {row[:5]}...")

    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    for path in csv_paths:
        check_csv(path)
