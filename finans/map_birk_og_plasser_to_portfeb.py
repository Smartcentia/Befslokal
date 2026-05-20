#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapper birk_og_plasser.csv mot Eiendomsportfeb.csv.
Bruker KUN kolonner for mapping: Region, EnhetID, Enhetsnavn, Enhetstype (Utledet),
Fylke, Kommune, Adresse, Postnummer, Poststed. Ingen andre kolonner leses eller brukes.
Rapporterer antall matchede rader og unike eiendommer.
"""
import csv
import re
import os

FINANS = os.path.dirname(os.path.abspath(__file__))
BIRK_PLASSER = os.path.join(FINANS, "birk _og_plasser.csv")
PORTFEB = os.path.join(FINANS, "Eiendomsportfeb.csv")

# Kun disse kolonnene brukes til mapping (jf. § 27 minnefil) – inkl. Enhetskorttype for å identifisere avdelinger
BIRK_MAPPING_COLS = [
    "Region", "EnhetID", "Enhetsnavn", "Enhetskorttype", "Enhetstype (Utledet)",
    "Fylke", "Kommune", "Adresse", "Postnummer", "Poststed",
]


def norm(s):
    if not s or not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def tokens(s):
    return set(re.sub(r"[^\w\s]", " ", s.lower()).split()) - {"og", "avd", "etg", "til", "postadresse", "postboks"}


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
                    poststed = (row.get("Poststed") or "").strip()
                    portfeb_rows.append({
                        "addr": addr,
                        "addr_linje": addr_linje,
                        "lok": lok,
                        "avtale": avtale,
                        "poststed": poststed,
                    })
            break
        except (UnicodeDecodeError, KeyError):
            continue

    # --- Les birk_og_plasser – kun mapping-kolonner (første rad er tom, andre er header) ---
    birk_rows = []
    with open(BIRK_PLASSER, newline="", encoding="latin-1") as f:
        next(f)  # hopp over tom første rad
        reader = csv.DictReader(f)
        for row in reader:
            b = {c: (row.get(c) or "").strip() for c in BIRK_MAPPING_COLS}
            if any(b.values()):
                birk_rows.append(b)

    # --- Match 1: Enhetsnavn mot Lokalisering/Avtalenavn (token-overlap) ---
    matches_name = []
    for b in birk_rows:
        navn = (b.get("Enhetsnavn") or "").strip()
        if len(navn) < 3:
            continue
        tb = tokens(navn)
        if not tb:
            continue
        for p in portfeb_rows:
            for ref in (p["lok"], p["avtale"]):
                if not ref:
                    continue
                tp = tokens(ref)
                overlap = tb & tp
                if len(overlap) >= 2 or (len(overlap) >= 1 and any(t.isdigit() for t in overlap)):
                    meaningful = overlap - {"gate", "vei", "veien", "gata", "avd", "etg"}
                    if len(meaningful) >= 1 or len(overlap) >= 2:
                        matches_name.append((b, p, "navn"))
                        break
            else:
                continue
            break

    # --- Match 2: Adresse + Postnummer ---
    matches_addr = []
    for b in birk_rows:
        adr = (b.get("Adresse") or "").strip()
        postnr = (b.get("Postnummer") or "").strip()
        if not adr or adr.lower().startswith("postboks"):
            continue
        adr_clean = re.sub(r"\s*Postadresse:.*", "", adr, flags=re.I).strip()
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
            p_post = re.search(r"\b(\d{4})\b", p["addr"] or "")
            pnr_ref = p_post.group(1) if p_post else ""
            if postnr and pnr_ref and postnr != pnr_ref:
                continue
            overlap = tb & tp
            if len(overlap) >= 2 or (len(overlap) >= 1 and any(t.isdigit() for t in overlap)):
                meaningful = overlap - {"gate", "vei", "veien", "gata", "gaten"}
                if len(meaningful) >= 1 or len(overlap) >= 2:
                    matches_addr.append((b, p, "adresse"))
                    break

    # --- Kombiner: unike (birk_rad, portfeb_lok) ---
    seen = set()
    match_details = []
    for b, p, typ in matches_name + matches_addr:
        key = (b.get("EnhetID"), b.get("Enhetsnavn"), p["lok"])
        if key in seen:
            continue
        seen.add(key)
        match_details.append((b, p, typ))

    matched_enhet_ids = {(b.get("EnhetID"), b.get("Enhetsnavn")) for b, p, _ in match_details}
    matched_portfeb_loks = {p["lok"] for _, p, _ in match_details}

    # --- Rapporter ---
    print("=== birk_og_plasser -> Eiendomsportfeb mapping (kun mapping-kolonner) ===\n")
    print(f"birk_og_plasser: {len(birk_rows)} rader (kun Region, EnhetID, Enhetsnavn, Enhetskorttype, Enhetstype, Fylke, Kommune, Adresse, Postnummer, Poststed)")
    avd_count = sum(1 for b in birk_rows if (b.get("Enhetskorttype") or "").strip() == "Avdeling")
    inst_count = sum(1 for b in birk_rows if (b.get("Enhetskorttype") or "").strip() == "Barnevernsinstitusjon")
    print(f"Avdelinger (Enhetskorttype=Avdeling): {avd_count} | Barnevernsinstitusjon: {inst_count} | Annet/tom: {len(birk_rows) - avd_count - inst_count}")
    print(f"Eiendomsportfeb: {len(portfeb_rows)} rader\n")
    print(f"Matchet på enhetsnavn: {len(matches_name)} birk-rader")
    print(f"Matchet på adresse:    {len(matches_addr)} birk-rader\n")
    print(f"Birk-rader med minst én match: {len(matched_enhet_ids)}")
    print(f"Unike Eiendomsportfeb-eiendommer matchet: {len(matched_portfeb_loks)}")
    print(f"Totalt unike (birk_rad, portfeb_lok)-par: {len(match_details)}\n")
    print("--- Eksempel (første 20) ---")
    for b, p, typ in match_details[:20]:
        navn = (b.get("Enhetsnavn") or "")[:40]
        adr = (b.get("Adresse") or "")[:35]
        print(f"  EnhetID {b.get('EnhetID')} | {navn} | {adr} -> {p['lok'][:45]} | ({typ})")
    unmatch = [b for b in birk_rows if (b.get("EnhetID"), b.get("Enhetsnavn")) not in matched_enhet_ids]
    if unmatch:
        print("\n--- Umatchede birk-rader (første 15) ---")
        for b in unmatch[:15]:
            print(f"  {b.get('EnhetID')}: {b.get('Enhetsnavn') or '(tom)'} | {b.get('Adresse') or '(tom)'}")


if __name__ == "__main__":
    main()
