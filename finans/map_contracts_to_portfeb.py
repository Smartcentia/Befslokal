#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapper contracts.csv mot Eiendomsportfeb.csv på adresse og Gnr/Bnr.
Rapporterer antall matchede rader og unike eiendommer.
"""
import csv
import re
import os

FINANS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(FINANS)
CONTRACTS = os.path.join(ROOT, "contracts.csv")
if not os.path.isfile(CONTRACTS):
    CONTRACTS = os.path.join(FINANS, "contracts.csv")
PORTFEB = os.path.join(FINANS, "Eiendomsportfeb.csv")


def tokens(s):
    if not s or not isinstance(s, str):
        return set()
    s = re.sub(r"[^\w\s]", " ", s.lower()).strip()
    return set(s.split()) - {"og", "avd", "etg", "til"}


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
                    portfeb_rows.append({
                        "addr": addr,
                        "addr_linje": addr_linje,
                        "gnr": gnr,
                        "bnr": bnr,
                        "lok": lok,
                    })
            break
        except UnicodeDecodeError:
            continue

    # --- Les contracts.csv ---
    contract_rows = []
    for path in (CONTRACTS, os.path.join(ROOT, "contracts.csv")):
        if not os.path.isfile(path):
            continue
        with open(path, newline="", encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            for row in r:
                nr = (row.get("#") or "").strip()
                region = (row.get("Region") or "").strip()
                adresse = (row.get("Adresse") or "").strip()
                gnr_bnr = (row.get("Gnr/Bnr") or "").strip()
                kontraktnr = (row.get("Kontraktnr") or "").strip()
                kategori = (row.get("Kategori") or "").strip()
                filnavn = (row.get("Filnavn (Kilde)") or "").strip()
                contract_rows.append({
                    "nr": nr,
                    "region": region,
                    "adresse": adresse,
                    "gnr_bnr": gnr_bnr,
                    "kontraktnr": kontraktnr,
                    "kategori": kategori,
                    "filnavn": filnavn,
                })
            break
        break

    # --- Match 1: Gnr/Bnr ---
    matches_gnr = []
    for c in contract_rows:
        gb = extract_gnr_bnr(c["gnr_bnr"])
        if not gb:
            continue
        g, bn = gb
        for p in portfeb_rows:
            if not p["gnr"] or not p["bnr"]:
                continue
            if p["gnr"] != g:
                continue
            pbnr = p["bnr"].replace(",", " ").replace(" og ", " ")
            if bn == p["bnr"] or bn in re.split(r"[\s()]+", pbnr):
                matches_gnr.append((c, p, "gnr_bnr"))
                break

    # --- Match 2: Adresse (token-overlap) ---
    matches_addr = []
    for c in contract_rows:
        if not c["adresse"] or len(c["adresse"]) < 5:
            continue
        tc = tokens(c["adresse"])
        if not tc:
            continue
        for p in portfeb_rows:
            tp = tokens(p["addr"] + " " + p["addr_linje"])
            if not tp:
                continue
            overlap = tc & tp
            if len(overlap) >= 2 or (len(overlap) >= 1 and any(t.isdigit() for t in overlap)):
                meaningful = overlap - {"gate", "vei", "veien", "gata", "gaten"}
                if len(meaningful) >= 1 or len(overlap) >= 2:
                    matches_addr.append((c, p, "adresse"))
                    break

    # --- Kombiner: unike (contract_rad, portfeb_lok) ---
    seen = set()
    match_details = []
    for c, p, typ in matches_gnr + matches_addr:
        key = (c["nr"], p["lok"])
        if key in seen:
            continue
        seen.add(key)
        match_details.append((c, p, typ))

    matched_contract_nrs = {m[0]["nr"] for m in match_details}
    matched_portfeb_loks = {m[1]["lok"] for m in match_details}

    # --- Rapporter ---
    print("=== contracts.csv -> Eiendomsportfeb mapping ===\n")
    print(f"contracts.csv:     {len(contract_rows)} rader")
    print(f"Eiendomsportfeb:   {len(portfeb_rows)} rader\n")
    print(f"Matchet på Gnr/Bnr:  {len(matches_gnr)} contract-rader")
    print(f"Matchet på adresse:  {len(matches_addr)} contract-rader\n")
    print(f"Contract-rader med minst én match: {len(matched_contract_nrs)}")
    print(f"Unike Eiendomsportfeb-eiendommer matchet: {len(matched_portfeb_loks)}")
    print(f"Totalt unike (contract_rad, portfeb_lok)-par: {len(match_details)}\n")
    print("--- Eksempel (første 30) ---")
    for c, p, typ in match_details[:30]:
        adr = (c["adresse"] or c["filnavn"])[:40]
        print(f"  #{c['nr']} {c['gnr_bnr'] or '-'} | {adr} -> {p['lok'][:45]} | ({typ})")
    print("\n--- Umatchede contract-rader (første 25) ---")
    unmatch = [c for c in contract_rows if c["nr"] not in matched_contract_nrs]
    for c in unmatch[:25]:
        adr = (c["adresse"] or c["filnavn"] or "(tom)")[:55]
        print(f"  #{c['nr']} {c['gnr_bnr'] or '-'}: {adr}")
    if len(unmatch) > 25:
        print(f"  ... og {len(unmatch) - 25} til.")


if __name__ == "__main__":
    main()
