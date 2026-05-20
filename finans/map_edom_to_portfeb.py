#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapper e-dom.txt (enheter) mot Eiendomsportfeb.csv på adresse+postnummer og Enhetsnavn.
Rapporterer antall matchede enheter og unike eiendommer.
"""
import csv
import re
import os

FINANS = os.path.dirname(os.path.abspath(__file__))
EDOM = os.path.join(FINANS, "e-dom.txt")
PORTFEB = os.path.join(FINANS, "Eiendomsportfeb.csv")


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
                    addr = (row.get("Adresse og Postnummer ") or row.get("Adresse og Postnummer") or "").strip()
                    addr_linje = (row.get("Adresselinje 1") or "").strip()
                    lok = (row.get("Lokalisering") or "").strip()
                    avtale = (row.get("Avtalenavn") or "").strip()
                    # Postnummer fra portfeb: "Gate 1, 0123 Sted" -> 0123
                    postnr = ""
                    m = re.search(r"\b(\d{4})\s+[A-Za-zÆØÅæøå]", addr)
                    if m:
                        postnr = m.group(1)
                    portfeb_rows.append({
                        "addr": addr,
                        "addr_linje": addr_linje,
                        "postnr": postnr,
                        "lok": lok,
                        "avtale": avtale,
                    })
            break
        except UnicodeDecodeError:
            continue

    # --- Les e-dom.txt (TSV, første linje "jeg gir deg alle dataene : \tHeader\t...") ---
    with open(EDOM, encoding="utf-8") as f:
        first = f.readline()
    header = first.split(" : ", 1)[-1].strip().split("\t")
    edom_rows = []
    with open(EDOM, encoding="utf-8") as f:
        f.readline()
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts.extend([""] * (len(header) - len(parts)))
            row = dict(zip(header, parts[: len(header)]))
            enhet_id = (row.get("EnhetID") or "").strip()
            enhetsnavn = (row.get("Enhetsnavn") or "").strip()
            adresse = (row.get("Adresse") or "").strip()
            postnummer = (row.get("Postnummer") or "").strip().replace(" ", "")
            poststed = (row.get("Poststed") or "").strip()
            region = (row.get("Region") or "").strip()
            edom_rows.append({
                "enhet_id": enhet_id,
                "enhetsnavn": enhetsnavn,
                "adresse": adresse,
                "postnummer": postnummer,
                "poststed": poststed,
                "region": region,
            })

    # --- Match 1: Adresse + Postnummer (samme postnr + token-overlap i adresse) ---
    matches_addr = []
    for e in edom_rows:
        if not e["adresse"] or len(e["adresse"]) < 4:
            continue
        te = tokens(e["adresse"])
        if not te:
            continue
        pnr = e["postnummer"]
        for p in portfeb_rows:
            if pnr and p["postnr"] and pnr != p["postnr"]:
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

    # --- Match 2: Enhetsnavn mot Lokalisering/Avtalenavn (token-overlap) ---
    matches_navn = []
    for e in edom_rows:
        if not e["enhetsnavn"] or len(e["enhetsnavn"]) < 4:
            continue
        te = tokens(e["enhetsnavn"])
        if not te or len(te) < 2:
            continue
        for p in portfeb_rows:
            tp = tokens(p["lok"] + " " + p["avtale"])
            if not tp:
                continue
            overlap = te & tp
            if len(overlap) >= 2:
                matches_navn.append((e, p, "navn"))
                break

    # --- Kombiner: unike (edom_enhet_id, portfeb_lok) ---
    seen = set()
    match_details = []
    for e, p, typ in matches_addr + matches_navn:
        key = (e["enhet_id"], p["lok"])
        if key in seen:
            continue
        seen.add(key)
        match_details.append((e, p, typ))

    matched_edom_ids = {m[0]["enhet_id"] for m in match_details}
    matched_portfeb_loks = {m[1]["lok"] for m in match_details}

    # --- Rapporter ---
    print("=== e-dom.txt -> Eiendomsportfeb mapping ===\n")
    print(f"e-dom enheter:      {len(edom_rows)} rader")
    print(f"Eiendomsportfeb:    {len(portfeb_rows)} rader\n")
    print(f"Matchet på adresse: {len(matches_addr)} e-dom-rader")
    print(f"Matchet på navn:   {len(matches_navn)} e-dom-rader\n")
    print(f"e-dom-rader med minst én match:     {len(matched_edom_ids)}")
    print(f"Unike Eiendomsportfeb-eiendommer:   {len(matched_portfeb_loks)}")
    print(f"Totalt unike (e-dom enhet, portfeb)-par: {len(match_details)}\n")
    print("--- Eksempel (første 25) ---")
    for e, p, typ in match_details[:25]:
        adr = (e["adresse"] or e["enhetsnavn"])[:40]
        print(f"  EnhetID {e['enhet_id']} | {adr} -> {p['lok'][:45]} | ({typ})")
    print("\n--- Umatchede e-dom-rader (første 20) ---")
    unmatch = [e for e in edom_rows if e["enhet_id"] not in matched_edom_ids]
    for e in unmatch[:20]:
        disp = (e["enhetsnavn"] or e["adresse"] or "(tom)")[:50]
        print(f"  {e['enhet_id']}: {disp}")
    if len(unmatch) > 20:
        print(f"  ... og {len(unmatch) - 20} til.")


if __name__ == "__main__":
    main()
