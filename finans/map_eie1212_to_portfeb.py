#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapper Eie1212.csv mot Eiendomsportfeb.csv KUN på eiendomsidentifikatorer
(Lokalisering, adresse, Matrikkel Gnr/Bnr). Bruker IKKE økonomitall.
"""
import csv
import re
import os

FINANS = os.path.dirname(os.path.abspath(__file__))
EIE1212 = os.path.join(FINANS, "Eie1212.csv")
PORTFEB = os.path.join(FINANS, "Eiendomsportfeb.csv")


def norm(s):
    if not s or not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s.lower().strip())


def tokens(s):
    if not s or not isinstance(s, str):
        return set()
    s = re.sub(r"[^\w\s]", " ", s.lower()).strip()
    return set(s.split()) - {"og", "avd", "etg", "til"}


def main():
    # --- Les Eiendomsportfeb ---
    portfeb_rows = []
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(PORTFEB, newline="", encoding=enc) as f:
                r = csv.DictReader(f)
                for row in r:
                    lok = (row.get("Lokalisering") or "").strip()
                    addr = (row.get("Adresse og Postnummer ") or row.get("Adresse og Postnummer") or "").strip()
                    addr_linje = (row.get("Adresselinje 1") or "").strip()
                    gnr = (row.get("Matrikkel Gnr") or "").strip()
                    bnr = (row.get("Matrikkel Bnr") or "").strip()
                    portfeb_rows.append({
                        "lok": lok,
                        "addr": addr,
                        "addr_linje": addr_linje,
                        "gnr": gnr,
                        "bnr": bnr,
                    })
            break
        except UnicodeDecodeError:
            continue

    # --- Les Eie1212 (semikolon) ---
    eie_rows = []
    with open(EIE1212, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f, delimiter=";")
        for row in r:
            lok = (row.get("Lokalisering") or "").strip()
            addr = (row.get("Adresse og Postnummer ") or row.get("Adresse og Postnummer") or "").strip()
            addr_linje = (row.get("Adresselinje 1") or "").strip()
            gnr = (row.get("Matrikkel Gnr") or "").strip()
            bnr = (row.get("Matrikkel Bnr") or "").strip()
            eie_rows.append({
                "lok": lok,
                "addr": addr,
                "addr_linje": addr_linje,
                "gnr": gnr,
                "bnr": bnr,
            })

    # --- Match 1: Lokalisering (normalisert likhet) ---
    portfeb_lok_norm = {norm(p["lok"]): p for p in portfeb_rows}
    matches_lok = []
    for e in eie_rows:
        if not e["lok"]:
            continue
        ek = norm(e["lok"])
        if ek in portfeb_lok_norm:
            p = portfeb_lok_norm[ek]
            matches_lok.append((e, p, "lokalisering"))

    # --- Match 2: Gnr + Bnr (matrikkel) ---
    matches_gnr = []
    for e in eie_rows:
        if not e["gnr"] or not e["bnr"]:
            continue
        for p in portfeb_rows:
            if not p["gnr"] or not p["bnr"]:
                continue
            if p["gnr"] != e["gnr"]:
                continue
            # Bnr kan være "237" eller "827 og 832"
            p_bnr = p["bnr"].replace(",", " ").replace(" og ", " ")
            if e["bnr"] == p["bnr"] or e["bnr"] in re.split(r"[\s()]+", p_bnr):
                matches_gnr.append((e, p, "gnr_bnr"))
                break

    # --- Match 3: Adresse + postnummer (token-overlap) ---
    postnr_re = re.compile(r"\b(\d{4})\s+[A-Za-zÆØÅæøå]")
    matches_addr = []
    for e in eie_rows:
        if not e["addr"] or len(e["addr"]) < 5:
            continue
        te = tokens(e["addr"] + " " + e["addr_linje"])
        if not te:
            continue
        m = postnr_re.search(e["addr"])
        e_pnr = m.group(1) if m else ""
        for p in portfeb_rows:
            p_m = postnr_re.search(p["addr"])
            p_pnr = p_m.group(1) if p_m else ""
            if e_pnr and p_pnr and e_pnr != p_pnr:
                continue
            tp = tokens(p["addr"] + " " + p["addr_linje"])
            if not tp:
                continue
            overlap = te & tp
            if len(overlap) >= 2 or (len(overlap) >= 1 and any(t.isdigit() for t in overlap)):
                meaningful = overlap - {"gate", "vei", "veien", "gata", "gaten"}
                if len(meaningful) >= 1 or len(overlap) >= 2:
                    matches_addr.append((e, p, "adresse"))
                    break

    # --- Kombiner: unike (eie_lok, portfeb_lok) ---
    seen = set()
    match_details = []
    for e, p, typ in matches_lok + matches_gnr + matches_addr:
        key = (e["lok"], p["lok"])
        if key in seen:
            continue
        seen.add(key)
        match_details.append((e, p, typ))

    matched_eie_loks = {m[0]["lok"] for m in match_details}
    matched_portfeb_loks = {m[1]["lok"] for m in match_details}

    # --- Rapporter ---
    print("=== Eie1212.csv -> Eiendomsportfeb (kun eiendomsmapping, ingen økonomi) ===\n")
    print(f"Eie1212:           {len(eie_rows)} rader")
    print(f"Eiendomsportfeb:   {len(portfeb_rows)} rader\n")
    print(f"Matchet på Lokalisering: {len(matches_lok)}")
    print(f"Matchet på Gnr/Bnr:      {len(matches_gnr)}")
    print(f"Matchet på adresse:      {len(matches_addr)}\n")
    print(f"Eie1212-rader med minst én match:   {len(matched_eie_loks)}")
    print(f"Unike Eiendomsportfeb-eiendommer:   {len(matched_portfeb_loks)}")
    print(f"Totalt unike (Eie1212, portfeb)-par: {len(match_details)}\n")
    print("--- Eksempel (første 25) ---")
    for e, p, typ in match_details[:25]:
        print(f"  {e['lok'][:50]} -> {p['lok'][:50]} | ({typ})")
    print("\n--- Umatchede Eie1212 Lokalisering (første 20) ---")
    unmatch = [e for e in eie_rows if e["lok"] not in matched_eie_loks]
    for e in unmatch[:20]:
        print(f"  {e['lok'][:60]}")
    if len(unmatch) > 20:
        print(f"  ... og {len(unmatch) - 20} til.")


if __name__ == "__main__":
    main()
