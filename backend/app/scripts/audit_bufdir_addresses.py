"""
Sammenligner kjente Bufdir-adresser (fra offisiell liste) mot properties-tabellen.
Produserer en avviksrapport i Markdown-format.

Kjøring:
    cd backend
    source .venv/bin/activate
    python -m app.scripts.audit_bufdir_addresses
"""
import asyncio
import sys
import os
from difflib import SequenceMatcher

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from sqlalchemy import text
from app.db.session import SessionLocal

# ── Offisiell Bufdir-adresseliste ──────────────────────────────────────────
BUFDIR_LOCATIONS = [
    {"label": "Bufdir (hovedkontor)",   "address": "Fredrik Selmers vei 3",  "postal": "0663", "city": "Oslo"},
    {"label": "Bufdir Alta",            "address": "Løkkeveien 33",           "postal": "9510", "city": "Alta"},
    {"label": "Bufdir Bergen",          "address": "Solheimsgaten 11",        "postal": "5058", "city": "Bergen"},
    {"label": "Bufdir Bodø",            "address": "Sjøgata 3",               "postal": "8006", "city": "Bodø"},
    {"label": "Bufdir Halden",          "address": "Violgata 8",              "postal": "1776", "city": "Halden"},
    {"label": "Bufdir Haugesund",       "address": "Rennesøygata 16",         "postal": "5537", "city": "Haugesund"},
    {"label": "Bufdir Kristiansand",    "address": "Tordenskjoldsgate 65",    "postal": "4605", "city": "Kristiansand"},
    {"label": "Bufdir Levanger",        "address": "Jernbanegata 11-13",      "postal": "7600", "city": "Levanger"},
    {"label": "Bufdir Lillestrøm",      "address": "Kanalveien 18",           "postal": "2004", "city": "Lillestrøm"},
    {"label": "Bufdir Nordfjordeid",    "address": "Sophus Lie Vegen 7",      "postal": "6770", "city": "Nordfjordeid"},
    {"label": "Bufdir Oslo (kontor)",   "address": "Fredrik Selmers vei 3",  "postal": "0663", "city": "Oslo"},
    {"label": "Bufdir Sjøvegan",        "address": "Eideveien 166",           "postal": "9350", "city": "Sjøvegan"},
    {"label": "Bufdir Stavanger",       "address": "Jåttåvegen 10",           "postal": "4020", "city": "Stavanger"},
    {"label": "Bufdir Trondheim",       "address": "Havnegata 9",             "postal": "7010", "city": "Trondheim"},
    {"label": "Bufdir Midt (Trondheim)","address": "Nordre gate 12",          "postal": "7011", "city": "Trondheim"},
    {"label": "Bufdir Tønsberg",        "address": "Anton Jenssensgt 5",      "postal": "3125", "city": "Tønsberg"},
]


def _normalize(s: str) -> str:
    return s.lower().strip().replace(",", "").replace(".", "").replace("-", " ")


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _match_address(official_addr: str, official_postal: str, db_rows: list) -> dict | None:
    """Prøver å finne beste treff i DB. Returnerer None hvis ingen god match."""
    best = None
    best_score = 0.0
    for row in db_rows:
        addr_db = row["address"] or ""
        postal_db = (row["postal_code"] or "").lstrip("0")
        postal_off = official_postal.lstrip("0")

        addr_score = _similarity(official_addr, addr_db)
        postal_match = postal_db == postal_off

        # Vektet: adresselikhet (60%) + postnummer-bonus (40%)
        score = addr_score * 0.6 + (0.4 if postal_match else 0)
        if score > best_score:
            best_score = score
            best = {**dict(row), "_score": score}

    return best if best_score >= 0.45 else None


async def audit():
    async with SessionLocal() as db:
        # Hent alle eiendommer med region = Bufdir ELLER region IS NULL (ukjent)
        result = await db.execute(text("""
            SELECT
                property_id::text,
                name,
                address,
                postal_code,
                city,
                region
            FROM properties
            WHERE LOWER(region) = 'bufdir'
               OR region IS NULL
               OR region = ''
            ORDER BY address
        """))
        bufdir_props = result.mappings().all()

        # Hent ALLE for bredere match-søk
        result_all = await db.execute(text("""
            SELECT
                property_id::text,
                name,
                address,
                postal_code,
                city,
                region
            FROM properties
            WHERE address IS NOT NULL
            ORDER BY address
        """))
        all_props = result_all.mappings().all()

    print(f"Eiendommer med region=Bufdir eller tom region: {len(bufdir_props)}")
    print(f"Totalt eiendommer med adresse: {len(all_props)}")
    print()

    matched = []
    not_found = []
    partial = []

    for loc in BUFDIR_LOCATIONS:
        # Prøv mot alle eiendommer
        hit = _match_address(loc["address"], loc["postal"], all_props)
        if hit and hit["_score"] >= 0.75:
            matched.append((loc, hit))
        elif hit and hit["_score"] >= 0.45:
            partial.append((loc, hit))
        else:
            not_found.append(loc)

    # ── Rapport ────────────────────────────────────────────────────────────
    lines = []
    lines.append("# Avviksrapport – Bufdir-adresser vs. properties-tabellen")
    lines.append(f"\n_Generert: 2026-02-21_\n")
    lines.append(f"**Offisielle Bufdir-lokasjoner:** {len(BUFDIR_LOCATIONS)}")
    lines.append(f"**Gode treff (score ≥ 0.75):** {len(matched)}")
    lines.append(f"**Svake/usikre treff (0.45–0.74):** {len(partial)}")
    lines.append(f"**Ikke funnet i DB:** {len(not_found)}")

    lines.append("\n---\n")
    lines.append("## ✅ Gode treff\n")
    lines.append("| Bufdir-lokasjon | Offisiell adresse | DB-adresse | DB-navn | Region i DB | Score |")
    lines.append("|---|---|---|---|---|---|")
    for loc, hit in matched:
        lines.append(
            f"| {loc['label']} | {loc['address']}, {loc['postal']} {loc['city']} "
            f"| {hit['address']}, {hit['postal_code']} {hit['city']} "
            f"| {hit['name'] or '–'} | {hit['region'] or '(tom)'} | {hit['_score']:.2f} |"
        )

    lines.append("\n---\n")
    lines.append("## ⚠️ Svake/usikre treff – krever manuell verifisering\n")
    lines.append("| Bufdir-lokasjon | Offisiell adresse | Beste DB-treff | DB-navn | Region i DB | Score |")
    lines.append("|---|---|---|---|---|---|")
    for loc, hit in partial:
        lines.append(
            f"| {loc['label']} | {loc['address']}, {loc['postal']} {loc['city']} "
            f"| {hit['address']}, {hit['postal_code']} {hit['city']} "
            f"| {hit['name'] or '–'} | {hit['region'] or '(tom)'} | {hit['_score']:.2f} |"
        )

    lines.append("\n---\n")
    lines.append("## ❌ Ikke funnet i databasen\n")
    lines.append("Disse lokasjonene mangler i properties-tabellen og må legges inn manuelt.\n")
    lines.append("| Bufdir-lokasjon | Adresse | Postnummer | By |")
    lines.append("|---|---|---|---|")
    for loc in not_found:
        lines.append(f"| {loc['label']} | {loc['address']} | {loc['postal']} | {loc['city']} |")

    lines.append("\n---\n")
    lines.append("## Eiendommer i DB med region=Bufdir\n")
    lines.append("| Navn | Adresse | Postnummer | By | Property ID |")
    lines.append("|---|---|---|---|---|")
    for row in bufdir_props:
        if str(row.get("region", "")).lower() == "bufdir":
            lines.append(
                f"| {row['name'] or '–'} | {row['address'] or '–'} "
                f"| {row['postal_code'] or '–'} | {row['city'] or '–'} | {row['property_id']} |"
            )

    report = "\n".join(lines)
    outfile = os.path.join(os.path.dirname(__file__), "bufdir_address_audit.md")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n\n📄 Rapport lagret: {outfile}")


if __name__ == "__main__":
    asyncio.run(audit())
