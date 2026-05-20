
import json
import os
from datetime import datetime

# Path to the BUP locations JSON file
BUP_JSON_PATH = "/Users/frank/BEFS3/KNOWME/backend/bup_lokasjoner_og_lenker.json"

# Scraped data from previous session (Consolidated from nbup.no and search)
# This is a sample of the data to be added. I will expand this list.
SCRAPED_LOCATIONS = {
    "helse_sor_ost": [
        {"navn": "BUP Grorud", "adresse": "Ammerudveien 45, 0958 Oslo", "telefon": "+47 22 16 82 00"},
        {"navn": "BUP Vest", "adresse": "Sognsvannsveien 21, 0372 Oslo", "telefon": "+47 22 11 80 00"},
        {"navn": "BUP Syd", "adresse": "Solveien 37, 1177 Oslo", "telefon": "+47 23 19 13 00"},
        {"navn": "BUP Nordre Aker", "adresse": "Nydalen allé 33, 0484 Oslo", "telefon": "+47 22 11 80 00"},
        {"navn": "BUP Follo", "adresse": "Ski sykehus, Vardeveien 15, 1400 Ski", "telefon": "+47 64 85 90 00"},
        {"navn": "BUP Asker", "adresse": "Kirkeveien 61, 1383 Asker", "telefon": "+47 67 50 20 00"},
        {"navn": "BUP Bærum", "adresse": "Dønskiveien 1, 1346 Gjettum", "telefon": "+47 67 50 20 00"},
        {"navn": "BUP Drammen", "adresse": "Dronninggata 28, 3019 Drammen", "telefon": "+47 32 80 30 00"},
        {"navn": "BUP Kongsvinger", "adresse": "Parkvegen 35, 2212 Kongsvinger", "telefon": "+47 62 88 77 00"},
        {"navn": "BUP Hamar", "adresse": "Furnesvegen 26, 2317 Hamar", "telefon": "+47 62 53 79 00"},
        {"navn": "BUP Lillehammer", "adresse": "Anders Sandvigs veg 17, 2609 Lillehammer", "telefon": "+47 61 27 20 00"},
        {"navn": "BUP Skien", "adresse": "Ulefossvegen 55, 3710 Skien", "telefon": "+47 35 00 31 00"},
        {"navn": "BUP Tønsberg", "adresse": "Kjelleveien 21, 3125 Tønsberg", "telefon": "+47 33 31 35 00"},
    ],
    "helse_vest": [
        {"navn": "BUP Bergen Sentrum", "adresse": "Ibsens gate 118, 5052 Bergen", "telefon": "+47 55 97 50 00"},
        {"navn": "BUP Fana", "adresse": "Nesttunbrekka 95, 5221 Nesttun", "telefon": "+47 55 91 84 00"},
        {"navn": "BUP Åsane", "adresse": "Litleåsvegen 2, 5132 Nyborg", "telefon": "+47 55 53 96 00"},
        {"navn": "BUP Stavanger", "adresse": "Armauer Hansens vei 20, 4011 Stavanger", "telefon": "+47 51 51 51 51"},
        {"navn": "BUP Haugesund", "adresse": "Karmsundgata 120, 5528 Haugesund", "telefon": "+47 52 73 20 00"},
        {"navn": "BUP Førde", "adresse": "Vievegen 34, 6807 Førde", "telefon": "+47 57 83 90 00"},
    ],
    "helse_midt": [
        {"navn": "BUP Trondheim", "adresse": "Klostertunet 1, 7030 Trondheim", "telefon": "+47 72 82 50 00"},
        {"navn": "BUP Levanger", "adresse": "Kirkegata 2, 7600 Levanger", "telefon": "+47 74 09 80 00"},
        {"navn": "BUP Namsos", "adresse": "Havnegata 40, 7800 Namsos", "telefon": "+47 74 21 54 00"},
        {"navn": "BUP Kristiansund", "adresse": "Herman Døhlens vei 1, 6508 Kristiansund", "telefon": "+47 71 12 00 00"},
        {"navn": "BUP Molde", "adresse": "Parkvegen 84, 6412 Molde", "telefon": "+47 71 12 00 00"},
        {"navn": "BUP Ålesund", "adresse": "Åsehaugen 5, 6017 Ålesund", "telefon": "+47 71 12 00 00"},
    ],
    "helse_nord": [
        {"navn": "BUP Tromsø", "adresse": "Hansine Hansens veg 14, 9019 Tromsø", "telefon": "+47 77 62 60 00"},
        {"navn": "BUP Bodø", "adresse": "Prinsens gate 164, 8005 Bodø", "telefon": "+47 75 53 40 00"},
        {"navn": "BUP Harstad", "adresse": "St. Olavs gate 70, 9406 Harstad", "telefon": "+47 77 01 50 00"},
        {"navn": "BUP Narvik", "adresse": "Sykehusveien 3, 8516 Narvik", "telefon": "+47 76 96 80 00"},
        {"navn": "BUP Alta", "adresse": "Markveien 31, 9510 Alta", "telefon": "+47 78 45 50 00"},
        {"navn": "BUP Hammerfest", "adresse": "Sykehusveien 35, 9600 Hammerfest", "telefon": "+47 78 42 10 00"},
        {"navn": "BUP Kirkenes", "adresse": "Skytterveien 14, 9900 Kirkenes", "telefon": "+47 78 97 30 00"},
    ]
}

def populate():
    if not os.path.exists(BUP_JSON_PATH):
        print(f"Error: {BUP_JSON_PATH} not found.")
        return

    with open(BUP_JSON_PATH, 'r') as f:
        data = json.load(f)

    # Backup original data
    with open(BUP_JSON_PATH + ".bak", 'w') as f:
        json.dump(data, f, indent=4)

    # Initialize locations if not present
    if "lokasjoner" not in data:
        data["lokasjoner"] = {}

    current_count = 0
    added_count = 0

    for region, locations in SCRAPED_LOCATIONS.items():
        if region not in data["lokasjoner"]:
            data["lokasjoner"][region] = []
        
        existing_addresses = {loc.get("adresse") for loc in data["lokasjoner"][region]}
        
        for loc in locations:
            if loc["adresse"] not in existing_addresses:
                # Add location with null lat/lon to be geocoded later
                new_loc = {
                    "navn": loc["navn"],
                    "adresse": loc["adresse"],
                    "telefon": loc.get("telefon", ""),
                    "latitude": None,
                    "longitude": None
                }
                data["lokasjoner"][region].append(new_loc)
                added_count += 1
            current_count += 1

    # Update metadata
    data["metadata"]["hentet_dato"] = datetime.now().isoformat()
    
    with open(BUP_JSON_PATH, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Successfully updated BUP locations.")
    print(f"Added: {added_count}")
    print(f"Total: {sum(len(v) for v in data['lokasjoner'].values())}")

if __name__ == "__main__":
    populate()
