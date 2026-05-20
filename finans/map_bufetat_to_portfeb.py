#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapper bufetat_eiendommer.csv mot Eiendomsportfeb.csv på adresse og Gnr_Bnr.
Rapporterer antall matchede rader og unike eiendommer.
"""
import csv
import re
import os

FINANS = os.path.dirname(os.path.abspath(__file__))
BUFETAT = os.path.join(FINANS, "bufetat_eiendommer.csv")
PORTFEB = os.path.join(FINANS, "Eiendomsportfeb.csv")


def norm(s):
    if not s or not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def tokens(s):
    return set(re.sub(r"[^\w\s]", " ", s.lower()).split()) - {"og", "avd", "etg", "til", "postadresse", "postboks"}


def extract_gnr_bnr(gnr_bnr):
    """Parse '44/54' or '47/384' -> (gnr, bnr) or None."""
    if not gnr_bnr or not isinstance(gnr_bnr, str):
        return None
    m = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*$", gnr_bnr.strip())
    if m:
        return (m.group(1), m.group(2))
    return None


def main():
    # --- Les Eiendomsportfeb ---
    portfeb_rows = []
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(PORTFEB, newline="", encoding=enc) as f:
                r = csv.DictReader(f)
                for row in r:
                    addr = (row.get("Adresse og Postnummer ") or row.get("Adresse og Postnummer") or "").strip()
                    addr_linje = (row.get("Adresselinje 1") or "").strip()
                    gnr = (row.get("Matrikkel Gnr") or "").strip()
                    bnr = (row.get("Matrikkel Bnr") or "").strip()
                    lok = (row.get("Lokalisering") or "").strip()
                    avtale = (row.get("Avtalenavn") or "").strip()
                    poststed = (row.get("Poststed") or "").strip()
                    portfeb_rows.append({
                        "addr": addr,
                        "addr_linje": addr_linje,
                        "gnr": gnr,
                        "bnr": bnr,
                        "lok": lok,
                        "avtale": avtale,
                        "poststed": poststed,
                    })
            break
        except UnicodeDecodeError:
            continue

    # --- Les bufetat_eiendommer ---
    bufetat_rows = []
    with open(BUFETAT, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            bid = (row.get("ID") or row.get("\ufeffID") or "").strip()
            adresse = (row.get("Adresse") or "").strip()
            kommune = (row.get("Kommune") or "").strip()
            region = (row.get("Region") or "").strip()
            gnr_bnr = (row.get("Gnr_Bnr") or "").strip()
            eienr = (row.get("Eiendomsnummer") or "").strip()
            kilde = (row.get("Kilde_dokument") or "").strip()
            bufetat_rows.append({
                "id": bid,
                "adresse": adresse,
                "kommune": kommune,
                "region": region,
                "gnr_bnr": gnr_bnr,
                "eiendomsnummer": eienr,
                "kilde": kilde,
            })

    # --- Match 1: Gnr_Bnr ---
    matches_gnr_bnr = []
    for b in bufetat_rows:
        gb = extract_gnr_bnr(b["gnr_bnr"])
        if not gb:
            continue
        g, bn = gb
        for p in portfeb_rows:
            if not p["gnr"] or not p["bnr"]:
                continue
            if p["gnr"] != g:
                continue
            # Bnr i portfeb kan være "2374" eller "783 og 411 (snr1 og 2)" – sjekk om bn finnes
            pbnr = p["bnr"].replace(",", " ").replace(" og ", " ")
            if bn == p["bnr"] or bn in re.split(r"[\s()]+", pbnr):
                matches_gnr_bnr.append((b, p, "gnr_bnr"))
                break

    # --- Match 2: Adresse (token-overlap) ---
    matches_addr = []
    for b in bufetat_rows:
        if not b["adresse"] or b["adresse"].startswith("Postboks"):
            continue
        adr_clean = re.sub(r"\s*Postadresse:\s*", "", b["adresse"])
        adr_clean = re.sub(r"\s*Gårdsnummer:.*", "", adr_clean, flags=re.I)
        adr_clean = adr_clean.strip()
        if len(adr_clean) < 5:
            continue
        tb = tokens(adr_clean)
        if not tb:
            continue
        for p in portfeb_rows:
            a1 = norm(p["addr"])
            a2 = norm(p["addr_linje"])
            tp = tokens(a1 + " " + a2)
            if not tp:
                continue
            overlap = tb & tp
            # Minst 2 felles token (f.eks. gatenavn + nummer) eller ett tall + ett navn
            if len(overlap) >= 2 or (len(overlap) >= 1 and any(t.isdigit() for t in overlap)):
                meaningful = overlap - {"gate", "vei", "veien", "gata", "gaten"}
                if len(meaningful) >= 1 or len(overlap) >= 2:
                    matches_addr.append((b, p, "adresse"))
                    break

    # --- Kombiner: unike (bufetat_rad, portfeb_lok) ---
    seen = set()
    match_details = []
    for b, p, typ in matches_gnr_bnr + matches_addr:
        key = (b["id"], p["lok"])
        if key in seen:
            continue
        seen.add(key)
        match_details.append((b, p, typ))

    matched_bufetat_ids = {m[0]["id"] for m in match_details}
    matched_portfeb_keys = {m[1]["lok"] for m in match_details}

    # --- Rapporter ---
    print("=== bufetat_eiendommer -> Eiendomsportfeb mapping ===\n")
    print(f"bufetat_eiendommer: {len(bufetat_rows)} rader")
    print(f"Eiendomsportfeb:   {len(portfeb_rows)} rader\n")
    print(f"Matchet på Gnr_Bnr:  {len(matches_gnr_bnr)} bufetat-rader")
    print(f"Matchet på adresse:  {len(matches_addr)} bufetat-rader\n")
    print(f"Bufetat-rader med minst én match: {len(matched_bufetat_ids)}")
    print(f"Unike Eiendomsportfeb-eiendommer matchet: {len(matched_portfeb_keys)}")
    print(f"Totalt unike (bufetat_rad, portfeb_lok)-par: {len(match_details)}\n")
    print("--- Eksempel (første 25) ---")
    for b, p, typ in match_details[:25]:
        disp = (b["adresse"] or b["kilde"] or "(tom)")[:45]
        print(f"  bufetat ID {b['id']} | {disp} | {b['gnr_bnr']} -> {p['lok'][:50]} | ({typ})")
    print("\n--- Umatchede bufetat-rader (ID, Adresse/Kilde) ---")
    unmatch = [b for b in bufetat_rows if b["id"] not in matched_bufetat_ids]
    for b in unmatch[:30]:
        disp = (b["adresse"] or b["kilde"] or "(tom)")[:60]
        print(f"  {b['id']}: {disp}")
    if len(unmatch) > 30:
        print(f"  ... og {len(unmatch) - 30} til.")

if __name__ == "__main__":
    main()
