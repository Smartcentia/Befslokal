import csv
import os

def check_headers():
    csv_path = os.path.join(os.getcwd(), 'backend', 'docs', 'Eiendom.csv')
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        print("HEADERS FOUND:")
        for h in reader.fieldnames:
             print(f"'{h}'")

if __name__ == "__main__":
    check_headers()
