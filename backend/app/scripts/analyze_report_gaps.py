import pandas as pd
import os

def analyze_report():
    file_path = "rapporttotalfeb2026.csv"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
    
    missing = df[df['EnhetID_ERP'].isna() | (df['EnhetID_ERP'] == '') | (df['EnhetID_ERP'] == 'nan')]
    
    print(f"=== Analyse av manglende EnhetID_ERP ({len(missing)} rader) ===")
    
    # 1. Lokasjonskode status
    has_loc = missing[missing['Lokasjonskode'].notna() & (missing['Lokasjonskode'] != '')]
    print(f"\nUten ERP, men MED Lokasjonskode: {len(has_loc)}")
    if not has_loc.empty:
        print("Topp 10 Lokasjonskoder som mangler ERP-kobling:")
        print(has_loc['Lokasjonskode'].value_counts().head(10))

    # 2. Region / Kommune fordeling
    print("\nTopp 10 Regioner:")
    print(missing['Region'].value_counts().head(10))
    
    print("\nTopp 10 Kommuner:")
    print(missing['Kommune'].value_counts().head(10))

    # 3. Kontraktstatus
    print("\nKontraktstatus for rader uten ERP:")
    print(missing['Kontrakt_Status'].value_counts())

    # 4. Adressetips (Sjekk om de ser ut som de burde vært matchet)
    print("\nEksempeladresser som mangler ERP:")
    print(missing[['Eiendom_Navn', 'Adresse']].drop_duplicates().head(15))

    # 5. Type bygg (Bruk)
    print("\nBruksområde (Bruk):")
    print(missing['Bruk'].value_counts().head(10))

if __name__ == "__main__":
    analyze_report()
