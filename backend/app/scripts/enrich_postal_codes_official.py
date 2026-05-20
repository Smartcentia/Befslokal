"""
Oppdaterer postnummer fra offisiell adresseliste (Bufetat-kilde).
Matcher DB-eiendommer mot den autorative listen og oppdaterer postal_code + city.
Overskriver evt. feil fra Kartverket-oppslaget.

Kjøring:
    cd backend
    python -m app.scripts.enrich_postal_codes_official
"""
import asyncio, sys, os, re
from difflib import SequenceMatcher

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from sqlalchemy import text
from app.db.session import SessionLocal

# ── Offisiell adresseliste fra Bufetat ────────────────────────────────────────
# Format: (gateadresse, poststed, postnummer)
OFFICIAL = [
    ("Korpåsen 172",              "ASKER",              "1386"),
    ("Rådhusgata 16",             "ASKIM",              "1830"),
    ("Liaveien 2",                "AURSKOG",            "1930"),
    ("Riserveien 40",             "AURSKOG",            "1930"),
    ("Strandsagvegen 2D",         "BRUMUNDDAL",         "2383"),
    ("Strandsagvegen 2 D",        "BRUMUNDDAL",         "2383"),
    ("Postboks 70",               "FAGERNES",           "2901"),
    ("Glemmengata 55",            "FREDRIKSTAD",        "1608"),
    ("Østheimveien 14",           "FREDRIKSTAD",        "1630"),
    ("Marmorveien 23",            "GJØVIK",             "2818"),
    ("Øverbyvegen 90",            "GJØVIK",             "2825"),
    ("Øverbyveien 90",            "GJØVIK",             "2819"),
    ("Storgata 10",               "GJØVIK",             "2815"),
    ("Øverbyvegen 80",            "GJØVIK",             "2819"),
    ("Storveien 121",             "GRESSVIK",           "1621"),
    ("Ugleveien 1",               "GRÅLUM",             "1712"),   # Kartverket ga feil (1554)
    ("Rokkeveien 849",            "HALDEN",             "1763"),
    ("Alfheimveien 6",            "HALDEN",             "1779"),
    ("Klukevegen 30",             "HAMAR",              "2318"),
    ("Fredvang allé 10",          "HAMAR",              "2321"),
    ("Fredvang alle 10",          "HAMAR",              "2321"),
    ("Vangsveien 121",            "HAMAR",              "2318"),
    ("Just Brochsgate 13",        "HAMAR",              "2321"),
    ("Just Brochs gate 13",       "HAMAR",              "2321"),
    ("Storgaten 11",              "HØNEFOSS",           "3510"),
    ("Storgata 11",               "HØNEFOSS",           "3510"),
    ("Åsaveien 662",              "HØNEFOSS",           "3512"),
    ("Åsaveien 663",              "HØNEFOSS",           "3512"),
    ("Bekkegata 2A",              "HØNEFOSS",           "3513"),
    ("Bekkegata 2 a",             "HØNEFOSS",           "3513"),
    ("Lundstadveien 30",          "HØNEFOSS",           "3514"),
    ("Askveien 132",              "HØNEFOSS",           "3519"),
    ("Ramsrudveien 32",           "HØNEFOSS",           "3518"),
    ("Husegutua 60",              "ILSENG",             "2344"),
    ("Trondheimsvegen 205",       "JESSHEIM",           "2050"),
    ("Trondheimsveien 205",       "JESSHEIM",           "2050"),
    ("Energivegen 14",            "JESSHEIM",           "2069"),
    ("Energiveien 14",            "JESSHEIM",           "2069"),
    ("Veiberggt. 2",              "JESSHEIM",           "2050"),
    ("Furubo, Finnskogveien",     "KIRKENÆR",           "2260"),
    ("Snorresveg 2",              "KIRKENÆR",           "2260"),
    ("Snorres veg 2",             "KIRKENÆR",           "2260"),
    ("Energiveien 13",            "KIRKENÆR",           "2260"),
    ("Energivegen 13",            "KIRKENÆR",           "2260"),
    ("Gågata 5",                  "KONGSVINGER",        "2211"),
    ("Storgata 56",               "LILLEHAMMER",        "2609"),
    ("Storgata 56-58",            "LILLEHAMMER",        "2609"),
    ("Kanalveien 18",             "LILLESTRØM",         "2004"),
    ("Torvet 6",                  "LILLESTRØM",         "2000"),
    ("Torget 6",                  "LILLESTRØM",         "2000"),
    ("Henrik Gernersgate 14",     "MOSS",               "1530"),
    ("Henrik Gerners gate 14",    "MOSS",               "1530"),
    ("Oscarsgate 20",             "OSLO",               "0352"),
    ("Grønlandsleiret 25",        "OSLO",               "0190"),
    ("Kabelgata 2",               "OSLO",               "0581"),
    ("Dronningensgate 8A",        "OSLO",               "0158"),
    ("Storgaten 21",              "OTTA",               "2670"),
    ("Nordsetvegen 227",          "REINSVOLL",          "2840"),
    ("Storveien 1408",            "RØMSKOG",            "1950"),
    ("Storveien 1404",            "RØMSKOG",            "1950"),
    ("Elias Smithsvei 24",        "SANDVIKA",           "1337"),
    ("Elias Smiths vei 22-24",    "SANDVIKA",           "1337"),
    ("Elias Smiths vei 24",       "SANDVIKA",           "1337"),
    ("Emma Hjorths vei 60",       "SANDVIKA",           "1336"),
    ("Emma Hjortsvei 60",         "SANDVIKA",           "1336"),
    ("Tokerudkollen 31-33",       "SANDVIKA",           "1336"),
    ("Kantarellveien 4",          "SARPSBORG",          "1708"),
    ("Kurlandveien 12",           "SARPSBORG",          "1727"),
    ("Skolegate 53",              "SARPSBORG",          "1724"),
    ("Skolegata 53",              "SARPSBORG",          "1724"),
    ("Idrettsveien 7",            "SKI",                "1400"),
    ("Glynitveien 30",            "SKI",                "1400"),
    ("Grimstadtunet 27",          "SKJEBERG",           "1746"),
    ("Grimestadveien 69",         "STOKKE",             "3160"),
    ("Dr. Thorshaugs veg 8",      "STANGE",             "2336"),
    ("Dr. Thorshaugsveg 8",       "STANGE",             "2336"),
    ("Dr. Torshaugsvei 8",        "STANGE",             "2336"),
    ("Sundløkkaveien 73",         "TORP",               "1659"),
    ("Aumliveien 4C",             "TYNSET",             "2500"),
    ("Njords vei 11",             "VESTBY",             "1541"),
    ("Bjørlistubben 14",          "VESTBY",             "1540"),
    ("Kroerveien 9",              "VESTBY",             "1541"),
    ("Solfallsveien 27",          "ÅS",                 "1435"),
    # ── Region Sør ────────────────────────────────────────────────────────────
    ("Nygårdsveien 49 B",         "ARENDAL",            "4844"),
    ("Nygårdsveien 49B",          "ARENDAL",            "4844"),
    ("Kirkegårdsveien 25",        "ARENDAL",            "4857"),  # Kartverket ga feil 4847
    ("Langsæveien 6",             "ARENDAL",            "4846"),
    ("Friholmsgaten 2-4",         "ARENDAL",            "4836"),
    ("Friholmsgata 2",            "ARENDAL",            "4836"),
    ("Kantarellveien 25",         "BARKÅKER",           "3157"),
    ("Justøyveien 493",           "BREKKESTØ",          "4780"),
    ("Wildhagens vei 17",         "DRAMMEN",            "3019"),
    ("Wildhagensvei 17",          "DRAMMEN",            "3019"),
    ("Grønland 68",               "DRAMMEN",            "3045"),
    ("Torvgt. 1",                 "FARSUND",            "4552"),
    ("Torvet 1",                  "FARSUND",            "4552"),
    ("Ilhaugveien 1",             "GEITHUS",            "3360"),
    ("Ilauveien 1",               "GEITHUS",            "3360"),
    ("Baneveien 19",              "HOKKSUND",           "3300"),  # Kartverket ga feil 0682 Oslo
    ("Haugsundgata 62",           "HOKKSUND",           "3303"),
    ("Frogsvei 19",               "KONGSBERG",          "3611"),
    ("Frogsvei 21-25",            "KONGSBERG",          "3611"),
    ("Tordenskjoldsgate 65",      "KRISTIANSAND S",     "4614"),
    ("Tordenskjolds gate 65",     "KRISTIANSAND S",     "4614"),
    ("Tordenskjoldsgate 65",      "KRISTIANSAND",       "4614"),
    ("Bispegra 52",               "KRISTIANSAND S",     "4632"),
    ("Markensgt. 35",             "KRISTIANSAND S",     "4612"),
    ("Markens gate 35",           "KRISTIANSAND S",     "4612"),
    ("Geiteramsveien 81",         "LARVIK",             "3268"),
    ("Geitramsveien 81",          "LARVIK",             "3268"),
    ("Solheiveien 25",            "LYNGDAL",            "4580"),
    ("Fr. Nansens vei 12",        "MANDAL",             "4514"),
    ("Fridtjof Nansensvei 12",    "MANDAL",             "4514"),
    ("Fridtjof Nansens vei 12",   "MANDAL",             "4514"),
    ("Nesverkveien 190",          "NES VERK",           "4934"),
    ("Thorøyaveien 5",            "SANDEFJORD",         "3209"),
    ("Thorøyaveien 1",            "SANDEFJORD",         "3209"),
    ("Torget 7",                  "SANDEFJORD",         "3210"),
    ("Brøløsvegen 51",            "SELJORD",            "3840"),
    ("Grinivegen 30D",            "SKIEN",              "3721"),
    ("Grinivegen 30",             "SKIEN",              "3721"),
    ("Gulsetringen 313",          "SKIEN",              "3742"),
    ("Kjørbekksvingen 38",        "SKIEN",              "3735"),
    ("Schweigaardsgate 11",       "SKIEN",              "3717"),
    ("Schweigaardsgt 11",         "SKIEN",              "3717"),
    ("Ulefossveien 52",           "SKIEN",              "3730"),
    ("Ulefossveien 53",           "SKIEN",              "3730"),  # mulig feil husnr i DB
    ("Solerødveien 50",           "SKOPPUM",            "3185"),
    ("Grimestadveien 69",         "STOKKE",             "3160"),
    ("Damtjernveien 598",         "SVARSTAD",           "3275"),
    ("Lundeveien 171",            "SØGNE",              "4640"),
    ("Kjelleveien 21",            "TØNSBERG",           "3103"),
    ("Anton Jenssensgate 2",      "TØNSBERG",           "3125"),
    ("Anton Jenssensgt. 2",       "TØNSBERG",           "3125"),
    ("Anton Jenssensgt 2",        "TØNSBERG",           "3125"),
    ("Haugetuft 16",              "VINJE",              "3890"),
    ("Haugetuft 16-18",           "VINJE",              "3890"),
    ("Torget 5",                  "ÅL",                 "3571"),

    # ── Region Vest ───────────────────────────────────────────────────────────
    ("Nedre Nattland 69",         "BERGEN",             "5099"),
    ("Solheimsgaten 11",          "BERGEN",             "5058"),
    ("Solheimsgaten 13",          "BERGEN",             "5058"),
    ("Solheimsgt 11",             "BERGEN",             "5058"),
    ("Bønesskogen 333",           "BØNES",              "5154"),
    ("Bønesstølen 13",            "BØNES",              "5154"),
    ("Flatøyvegen 45",            "FREKHAUG",           "5918"),
    ("Vestlundveien 22a",         "FYLLINGSDALEN",      "5145"),
    ("Vestlundveien 22A",         "FYLLINGSDALEN",      "5145"),
    ("Bregnetunet 15",            "FØRDE",              "6812"),
    ("Svanehaugvegen 3",          "FØRDE",              "6812"),
    ("Storehagen 1b",             "FØRDE",              "6800"),
    ("Storehagen 1B",             "FØRDE",              "6800"),
    ("Kompani Lingesvei 23",      "HAFRSFJORD",         "4045"),
    ("Rennesøygata 16",           "HAUGESUND",          "5537"),
    ("Haraldsgata 94",            "HAUGESUND",          "5528"),
    ("Skinflorbakkane 12",        "MJØLKERÅEN",         "5136"),
    ("Nybøveien 24",              "NESTTUN",            "5221"),
    ("Skjoldvegen 51",            "NESTTUN",            "5221"),
    ("Sophus Lie-vegen 9",        "NORDFJORDEID",       "6770"),
    ("Sophus Lievegen 9",         "NORDFJORDEID",       "6770"),
    ("Sophus Lie-vegen 5",        "NORDFJORDEID",       "6770"),
    ("Almerket 30",               "ODDA",               "5750"),
    ("Røldalsvegen 2",            "ODDA",               "5750"),
    ("Sandbrekkevegen 27",        "PARADIS",            "5231"),
    ("Sandbrekkvegen 27",         "PARADIS",            "5231"),
    ("Aurdalslia 96",             "SANDSLI",            "5253"),
    ("Rødstokken 16",             "SOGNDAL",            "6856"),
    ("Torleiv Kvalviksgt. 9",     "STAVANGER",          "4022"),
    ("Torleiv Kvalviks gate 9",   "STAVANGER",          "4022"),
    ("Rogalandsgt. 18",           "STAVANGER",          "4011"),
    ("Rogalandsgata 18",          "STAVANGER",          "4011"),
    ("Lindøy 9",                  "STAVANGER",          "4013"),  # Kartverket ga 4075
    ("Jåttåvågveien 10",          "STAVANGER",          "4020"),
    ("Jåttåvegen 10",             "STAVANGER",          "4020"),
    ("Torget 10",                 "STORD",              "5417"),
    ("Haugane 15",                "SØFTELAND",          "5212"),
    ("Feråsvegen 13",             "SØREIDGREND",        "5251"),
    ("Tertneshøyden 33b",         "TERTNES",            "5113"),
    ("Tertneshøyden 33B",         "TERTNES",            "5113"),
    ("Uttrågata 36",              "VOSS",               "5700"),
    ("Humlevegen 92",             "ÅLESUND",            "6020"),
    ("Husafjellet 6",             "ÅLESUND",            "6009"),
    ("Vågeveien 10",              "KRISTIANSUND N",     "6509"),
    ("Furene 8",                  "VOLDA",              "6105"),

    # ── Region Midt-Norge ─────────────────────────────────────────────────────
    ("Hanskleiva 25",             "BUVIKA",             "7350"),
    ("Ljåmovegen 10",             "FANNREM",            "7320"),
    ("Ljåmovein 10",              "FANNREM",            "7320"),
    ("Kvalvågveien 113",          "FREI",               "6521"),
    ("Konstadlykkjveien 55",      "GÅSBAKKEN",          "7213"),
    ("Vågeveien 10",              "KRISTIANSUND N",     "6509"),
    ("Jernbanegata 11-13",        "LEVANGER",           "7600"),
    ("Jernbanegata 11/13",        "LEVANGER",           "7600"),
    ("Arne Vestrums veg 1A",      "LEVANGER",           "7604"),
    ("Hølondvegen 311",           "MELHUS",             "7224"),
    ("Hølondveien 311",           "MELHUS",             "7224"),
    ("Storgata 12-14",            "MOLDE",              "6413"),
    ("Storgata 12 - 14",          "MOLDE",              "6413"),  # Kartverket ga feil 1870 Ørje
    ("Frænaveien 16",             "MOLDE",              "6415"),
    ("Frænaveigen 16",            "MOLDE",              "6415"),
    ("Abel Meyers gate 10",       "NAMSOS",             "7800"),
    ("Theodor Owerviensveg 16",   "RANHEIM",            "7055"),
    ("Peder Myhres vei 16",       "RANHEIM",            "7055"),
    ("Forbordsfjellvegen 119",    "SKATVAL",            "7510"),
    ("Fordbordsfjellveien 119",   "SKATVAL",            "7510"),
    ("Grønlihøgda 24",            "SPILLUM",            "7820"),
    ("Bomveien 3",                "STEINKJER",          "7725"),  # Kartverket ga feil 0782 Oslo
    ("Kirkeveien 33",             "STJØRDAL",           "7514"),
    ("Kirkevegen 33",             "STJØRDAL",           "7514"),
    ("Havnegata 9",               "TRONDHEIM",          "7010"),
    ("Nordre gate 12",            "TRONDHEIM",          "7011"),
    ("Nordregate 12",             "TRONDHEIM",          "7011"),
    ("Åsvangveien 2A",            "TRONDHEIM",          "7049"),
    ("Åsvangveien 2",             "TRONDHEIM",          "7049"),
    ("Østmarkveien 26 D/E",       "TRONDHEIM",          "7040"),
    ("Østmarkveien 26D",          "TRONDHEIM",          "7040"),
    ("Myrakollen 2",              "VESTNES",            "6390"),
    ("Vikhovlia 1400",            "VIKHAMMER",          "7560"),
    ("Nygårdsvegen 2",            "VOLDA",              "6103"),
    ("Nygardsvegen 2",            "VOLDA",              "6103"),
    ("Klatrevegen 2",             "VOLDA",              "6104"),
    ("Furene 8",                  "VOLDA",              "6105"),
    ("Humlevegen 92",             "ÅLESUND",            "6020"),
    ("Humlavegen 92",             "ÅLESUND",            "6020"),
    ("Langelandsveien 17",        "ÅLESUND",            "6010"),
    ("Husafjellet 6",             "ÅLESUND",            "6009"),

    # ── Region Nord ───────────────────────────────────────────────────────────
    ("Løkkeveien 33",             "ALTA",               "9515"),  # DB har 9510 fra Kartverket
    ("Strandveien 6-14",          "ALTA",               "9513"),
    ("Strandvn 6",                "ALTA",               "9513"),
    ("Nordstrandveien 41",        "BODØ",               "8012"),
    ("Storgata 27/29",            "BODØ",               "8006"),  # Kartverket ga feil 9900 Kirkenes
    ("Storgata 27/29 ",           "BODØ",               "8006"),
    ("Storgata 27",               "BODØ",               "8006"),
    ("Rønvikveien 9A",            "BODØ",               "8009"),
    ("Rønvikvn 9A",               "BODØ",               "8009"),
    ("Skoleveien 9",              "BODØ",               "8009"),
    ("Heimlyveien 5",             "BORKENES",           "9475"),  # Kartverket ga feil 1920 Sørumsand
    ("Heimlyvn 5",                "BORKENES",           "9475"),
    ("Røvikveien 21",             "FAUSKE",             "8214"),
    ("Hans Karolius vei 6",       "FINNSNES",           "9300"),
    ("Sørøygata 10",              "HAMMERFEST",         "9600"),
    ("Sørøygt 10",                "HAMMERFEST",         "9600"),
    ("Håkonsgate 4",              "HARSTAD",            "9405"),
    ("Håkonsgt. 4",               "HARSTAD",            "9405"),
    ("Håkonsgt 4",                "HARSTAD",            "9405"),
    ("Fitnudatgeaidnu 41-43",     "KARASJOK",           "9730"),
    ("Fitnodatgeaidnu 41-43",     "KARASJOK",           "9730"),
    ("Pasvikveien 2",             "KIRKENES",           "9900"),
    ("Wiulls gate 3",             "KIRKENES",           "9900"),
    ("Håkøyveien 339",            "KVALØYA",            "9109"),
    ("Håkøyvn 339",               "KVALØYSLETTA",       "9109"),
    ("Brennstadmoen 23",          "MO I RANA",          "8614"),
    ("Kongens gate 51-55",        "NARVIK",             "8514"),
    ("Kongensgate 51",            "NARVIK",             "8514"),
    ("Torolv Kveldulvsons gate 39","SANDNESSJØEN",      "8800"),
    ("Torolv Kveldulvsonsgt 39",  "SANDNESSJØEN",       "8800"),
    ("Islandsbotnveien 35",       "SILSAND",            "9303"),
    ("Eideveien 168",             "SJØVEGAN",           "9350"),
    ("Eideveien 166",             "SJØVEGAN",           "9350"),
    ("Idrettsveien 5",            "SORTLAND",           "8402"),
    ("Idrettsvn 5",               "SORTLAND",           "8402"),
    ("Markedsgata 20",            "STOKMARKNES",        "8450"),
    ("Markedsgt 20",              "STOKMARKNES",        "8450"),
    ("Storgata 70",               "TROMSØ",             "9008"),
    ("Kaigata 4",                 "TROMSØ",             "9008"),
    ("Solbakken 12",              "TROMSØ",             "9006"),
    ("Grensen 7",                 "VADSØ",              "9800"),
    ("Fiskergata 22",             "SVOLVÆR",            "8300"),
    ("Brennstadmoen 23",          "MO I RANA",          "8614"),

    # ── Bufdir-kontor-adresser ─────────────────────────────────────────────
    ("Anton Jensens gate 5",      "TØNSBERG",           "3125"),
    ("Anton Jenssens gate 2",     "TØNSBERG",           "3125"),
    ("Anton Jensensgt 5",         "TØNSBERG",           "3125"),
    ("Anton Jenssensgt 5",        "TØNSBERG",           "3125"),
    ("Fredrik Selmers vei 3",     "OSLO",               "0663"),
    ("Tordenskjoldsgate 65",      "KRISTIANSAND S",     "4605"),
    ("Tordenskjoldsgt. 65",       "KRISTIANSAND S",     "4605"),
]

# Bygg oppslag: normalisert adresse → postnummer + by
def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)
    s = s.replace('.', '').replace(',', '')
    return s

LOOKUP: dict[str, tuple[str, str]] = {}
for addr, city, postal in OFFICIAL:
    LOOKUP[_norm(addr)] = (postal, city.title())


def _best_match(db_addr: str, db_city: str) -> tuple[str, str] | None:
    """Finn beste match i LOOKUP for en DB-adresse."""
    na = _norm(db_addr)
    nc = _norm(db_city or "")

    # 1. Eksakt treff
    if na in LOOKUP:
        return LOOKUP[na]

    # 2. DB-adresse er et prefiks av offisiell adresse (eller omvendt)
    for off_addr, (postal, off_city) in LOOKUP.items():
        if _norm(off_city) != nc and nc:
            continue
        if na.startswith(off_addr) or off_addr.startswith(na):
            return (postal, off_city)

    # 3. Fuzzy likhet >= 0.82
    best_score = 0.0
    best_val = None
    for off_addr, (postal, off_city) in LOOKUP.items():
        if _norm(off_city) != nc and nc:
            continue
        score = SequenceMatcher(None, na, off_addr).ratio()
        if score > best_score:
            best_score = score
            best_val = (postal, off_city)
    if best_score >= 0.82:
        return best_val

    return None


async def enrich():
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT property_id::text, name, address, postal_code, city
            FROM properties
            WHERE address IS NOT NULL
            ORDER BY address
        """))
        props = result.mappings().all()

    updated = []
    corrected = []  # properties that had a postal but it was wrong
    no_match = []

    for p in props:
        addr = p["address"] or ""
        city = p["city"] or ""
        existing = p["postal_code"]

        match = _best_match(addr, city)
        if not match:
            if not existing:
                no_match.append(p)
            continue

        new_postal, new_city = match

        if existing == new_postal:
            continue  # allerede riktig

        action = "korrigert" if existing else "ny"
        entry = {
            "property_id": p["property_id"],
            "postal_code": new_postal,
            "city": new_city,
            "address": addr,
            "old_postal": existing,
        }
        if existing:
            corrected.append(entry)
            print(f"[KORRIGER] {addr}, {city}: {existing} → {new_postal} ({new_city})")
        else:
            updated.append(entry)
            print(f"[NY]       {addr}, {city}: → {new_postal} ({new_city})")

    all_updates = updated + corrected
    print(f"\n--- Oppsummering ---")
    print(f"Nye postnumre:      {len(updated)}")
    print(f"Korrigerte:         {len(corrected)}")
    print(f"Fortsatt mangler:   {len(no_match)}")

    if all_updates:
        print(f"\nSkriver {len(all_updates)} oppdateringer...")
        async with SessionLocal() as db:
            for row in all_updates:
                await db.execute(text("""
                    UPDATE properties
                    SET postal_code = :postal, city = :city
                    WHERE property_id = CAST(:pid AS uuid)
                """), {"postal": row["postal_code"], "city": row["city"], "pid": row["property_id"]})
            await db.commit()
        print("✅ Database oppdatert.")

    # Sluttelling
    async with SessionLocal() as db:
        r = await db.execute(text("SELECT COUNT(*) FROM properties WHERE postal_code IS NOT NULL"))
        have = r.scalar()
        r2 = await db.execute(text("SELECT COUNT(*) FROM properties"))
        total = r2.scalar()
    print(f"\n📊 Totalt: {have}/{total} eiendommer har postnummer ({have/total*100:.0f}%)")

    if no_match:
        print(f"\nGjenstående uten treff ({len(no_match)}):")
        for p in no_match:
            print(f"  - {p['address']}, {p['city']}")

    # ── Generer rapport over alle eiendommer uten postnummer ────────────────
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT property_id::text, name, address, postal_code, city, region
            FROM properties
            WHERE postal_code IS NULL
            ORDER BY city, address
        """))
        still_missing = result.mappings().all()

    report_lines = [
        "# Rapport: Eiendommer uten postnummer",
        "",
        f"_Oppdatert: 2026-02-21 – etter import av Region Øst-adresser_",
        "",
        f"**Totalt mangler:** {len(still_missing)} eiendommer",
        "",
        "Disse krever manuell verifisering eller mangler i offisielle adresselister.",
        "Sannsynlig årsak per rad er angitt i merknad-kolonnen.",
        "",
        "| # | Navn | Adresse | By | Region | Merknad |",
        "|---|---|---|---|---|---|",
    ]

    KNOWN_ISSUES = {
        "Rokkeveien 502":       "Mulig feil husnr – offisiell liste har nr. 849",
        "Egge gård":            "Gårdsnavn uten husnummer",
        "Lindøy 9":             "Øy-adresse – ikke i matrikkelen",
        "Furubo, Finnskogveien":"Gårdsnavn/sted uten gate",
        "Postboks 70":          "Postboks – ingen fysisk adresse",
    }

    for i, row in enumerate(still_missing, 1):
        addr = row["address"] or "–"
        merknad = next((v for k, v in KNOWN_ISSUES.items() if k.lower() in addr.lower()), "Ikke funnet i noen adresseliste")
        report_lines.append(
            f"| {i} | {row['name'] or '–'} | {addr} | {row['city'] or '–'} | {row['region'] or '–'} | {merknad} |"
        )

    report_lines += [
        "",
        "---",
        "",
        "## Neste steg",
        "",
        "- [ ] Motta adresselister for Region Nord, Midt-Norge, Vest, Sør og Bufdir",
        "- [ ] Korriger adresser med feil husnummer (Rokkeveien 502 → 849?)",
        "- [ ] Legg inn Bufdir-kontor som mangler (Bodø, Halden, Nordre gate Trondheim)",
    ]

    report_path = os.path.join(os.path.dirname(__file__), "manglende_postnummer.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n📄 Rapport lagret: {report_path}")


if __name__ == "__main__":
    asyncio.run(enrich())
