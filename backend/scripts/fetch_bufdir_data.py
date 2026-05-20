"""
Hent barnevernsinstitusjoner fra bufdir.no/barnevern/finn-institusjon/.
Støtter automatisk henting med paginering (httpx) eller lesing fra lokal HTML (plan B).

Bufdir-pipeline (kjør fra prosjektrot i denne rekkefølgen):
  1. python backend/scripts/fetch_bufdir_data.py [--default-filters | --query "..."]
       → backend/bufdir_institutions.json
  2. python backend/scripts/scrape_bufdir_institution_pages.py
       → backend/bufdir_institutions_detailed.json (galleri, seksjoner, kontakt)
  3. python backend/scripts/match_bufdir_robust.py
       → backend/bufdir_matches_robust.json (+ bufdir_matches_uncertain.json, bufdir_unmatched.json)
  4. python backend/scripts/enrich_properties_bufdir.py
       → oppdaterer DB (external_data.bufdir, valgfritt navn/beskrivelse, bilder under frontend/public/bufdir_images/)

Kjør:
  python backend/scripts/fetch_bufdir_data.py [--local] [--out path.json]
  python backend/scripts/fetch_bufdir_data.py --query "institutionOwnerShipType=1%3B2%3B3%3B4&..."

Standard filter (alle eierformer, alle regioner, alle institusjonstyper) kan aktiveres med --default-filters.
"""
import argparse
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode

logging.basicConfig(level=logging.INFO, stream=__import__("sys").stdout)
logger = logging.getLogger(__name__)

URL_BASE = "https://www.bufdir.no/barnevern/finn-institusjon/"
# Script ligger i backend/scripts/; skriv til backend/bufdir_institutions.json (prosjektrot = parent.parent.parent)
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
OUTPUT_FILE = BACKEND_DIR / "bufdir_institutions.json"

USER_AGENT = "BEFS-Eiendomsbase/1.0 (dataoppdatering barnevernsinstitusjoner)"
PAGE_DELAY_SEC = 1.5

# Samme utvalg som typisk brukt i Bufdir-listen (semikolon i verdier URL-kodes som %3B)
DEFAULT_LIST_QUERY = (
    "institutionOwnerShipType=1%3B2%3B3%3B4"
    "&institutionRegions=1%3B2%3B3%3B4%3B5"
    "&institutionTypeIds=1%3B2%3B3%3B4%3B5"
)


def build_list_url(page: int = 1, extra_query: Optional[str] = None) -> str:
    """
    Liste-URL med valgfrie filter-parametre. Side 1 utelater page= (med mindre brukt i extra_query).
    Side >1 setter page=N (overskriver evt. page i extra_query).
    """
    if not extra_query or not str(extra_query).strip():
        return URL_BASE if page <= 1 else f"{URL_BASE}?page={page}"
    q = str(extra_query).strip().lstrip("?")
    pairs = dict(parse_qsl(q, keep_blank_values=True))
    if page > 1:
        pairs["page"] = str(page)
    else:
        pairs.pop("page", None)
    return f"{URL_BASE}?{urlencode(pairs, doseq=True)}"


def parse_institutions_from_html(html: str) -> list:
    """Hent ut institutions-array fra HTML (JSON-blokk). Returnerer liste med rå objekter."""
    unescaped = html.replace('\\"', '"')
    target_start = '"institutions":['
    start_idx = unescaped.find(target_start)
    if start_idx == -1:
        return []
    start_content = start_idx + len(target_start)
    bracket_count = 1
    end_idx = start_content
    for i in range(start_content, len(unescaped)):
        if unescaped[i] == "[":
            bracket_count += 1
        elif unescaped[i] == "]":
            bracket_count -= 1
        if bracket_count == 0:
            end_idx = i
            break
    array_content = unescaped[start_content:end_idx]
    items_str = array_content.split("},{")
    if len(items_str) > 1:
        items_str[0] = items_str[0] + "}"
        items_str[-1] = "{" + items_str[-1]
        for k in range(1, len(items_str) - 1):
            items_str[k] = "{" + items_str[k] + "}"
    all_items = []
    for s in items_str:
        if not s.startswith("{"):
            s = "{" + s
        if not s.endswith("}"):
            s = s + "}"
        try:
            all_items.append(json.loads(s))
        except Exception:
            pass
    return all_items


def fetch_page(page: int = 1, extra_query: Optional[str] = None) -> Optional[str]:
    """Hent én side HTML fra bufdir.no."""
    try:
        import httpx
    except ImportError:
        logger.error("httpx mangler. Installer med: pip install httpx")
        return None
    url = build_list_url(page, extra_query)
    try:
        with httpx.Client(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        logger.warning("Request failed for %s: %s", url, e)
        return None


def fetch_all_pages(extra_query: Optional[str] = None) -> list:
    """Hent alle sider med paginering til ingen nye institusjoner kommer."""
    seen_ids = set()
    all_items = []
    page = 1
    while True:
        logger.info("Henter side %s...", page)
        html = fetch_page(page, extra_query)
        if not html:
            break
        items = parse_institutions_from_html(html)
        if not items:
            break
        new_count = 0
        for it in items:
            iid = it.get("id")
            if iid is not None and iid not in seen_ids:
                seen_ids.add(iid)
                all_items.append(it)
                new_count += 1
        logger.info("Side %s: %s nye (totalt %s)", page, new_count, len(all_items))
        if new_count == 0:
            break
        page += 1
        time.sleep(PAGE_DELAY_SEC)
    return all_items


def fetch_local_fallback() -> list:
    """Plan B: les fra lokal bufdir_source.html (evt. bufdir_source_page1.html, ...)."""
    seen_ids = set()
    all_items = []
    for p in [SCRIPT_DIR / "bufdir_source.html"] + [
        SCRIPT_DIR / f"bufdir_source_page{i}.html" for i in range(1, 12)
    ]:
        if not p.exists():
            continue
        logger.info("Leser %s...", p.name)
        try:
            html = p.read_text(encoding="utf-8")
            items = parse_institutions_from_html(html)
            for it in items:
                iid = it.get("id")
                if iid is not None and iid not in seen_ids:
                    seen_ids.add(iid)
                    all_items.append(it)
        except Exception as e:
            logger.warning("Kunne ikke lese %s: %s", p.name, e)
    return all_items


def main():
    parser = argparse.ArgumentParser(description="Hent bufdir barnevernsinstitusjoner")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Bruk kun lokal HTML (bufdir_source.html osv.) i stedet for live-fetch",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help=(
            "Query-streng for listevisning (uten ledende ?), f.eks. "
            "institutionOwnerShipType=1%%3B2&institutionRegions=1%%3B2&institutionTypeIds=1%%3B2&page=10"
        ),
    )
    parser.add_argument(
        "--default-filters",
        action="store_true",
        help=f"Bruk standard filter (alle typer/regioner). Tilsvarende: {DEFAULT_LIST_QUERY[:50]}...",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUTPUT_FILE,
        help=f"JSON-fil (standard: {OUTPUT_FILE})",
    )
    args = parser.parse_args()

    list_query: Optional[str] = None
    if args.default_filters:
        list_query = DEFAULT_LIST_QUERY
    if args.query:
        list_query = args.query

    if args.local:
        raw_items = fetch_local_fallback()
    else:
        raw_items = fetch_all_pages(list_query)
        if not raw_items:
            logger.warning("Ingen data fra live-fetch; prøver lokal fallback.")
            raw_items = fetch_local_fallback()

    if not raw_items:
        logger.error("Ingen institusjoner funnet. Kjør med --local etter å ha lagret HTML.")
        return

    logger.info("Totalt %s institusjoner. Lagrer...", len(raw_items))
    save_data(raw_items, args.out)

def save_data(data, outfile: Path):
    processed = []
    
    # Legal paragraph mapping
    # The keys in "institutionTypes" might look like "Atferd §§ 6-1 og 6-2"
    # User Rules:
    # Akutt §§ 4-1 og 4-2 (tidligere §§ 4-6,1 og 4-6,2)
    # Akutt § 4-4 (tidligere § 4-25,2 jfr. § 4-24)
    # Atferd §§ 6-1 og 6-2 (tidligere §§ 4-24 og 4-26)
    # Omsorg §§ 3-2 og 5-1 (tidligere §§ 4-12 og 4-4,6)
    
    # We will store what we find, and maybe add a "mapped_types" field?
    # Or just replace text if we see the old ones.
    # The website seems to have NEW ones (e.g. "Omsorg §§ 3-2 og 5-1").
    # So we mainly need to ensure we capture them.
    
    # We will log what we find to see if any old ones appear.
    
    for item in data:
         image = item.get("image") or {}
         # Flere fallbacks – bufdir kan bruke url, desktopUrl, mobileUrl, src, imageUrl
         image_url = (
             image.get("url")
             or image.get("desktopUrl")
             or image.get("mobileUrl")
             or image.get("src")
             or image.get("imageUrl")
         )
         
         # Description is sometimes in 'intro' or 'description' or 'addressInformation' (nope)
         # In the snippet: 'intro' wasn't visible but 'heading' was.
         # Actually snippet had: "pageName", "heading", "institutionTypes", "addressInformation"
         # It didn't show 'intro' or 'description' explicitly in my short snippet, but typically it's there.
         # Let's use 'description' if exists, else empty.
         
         inst = {
             "name": item.get("heading") or item.get("pageName"),
             "address": item.get("addressInformation"), 
             "description": item.get("intro") or item.get("description") or "", 
             "legal_bases": item.get("institutionTypes", []),
             "image_url": image_url,
             "bufdir_url": item.get("linkToInstitution"),
             "owner_type": item.get("institutionOwnerShipType"),
             "id": item.get("id"),
             "email": item.get("email"),
             "phone": item.get("phoneNumber"),
             "location": item.get("location")
         }
         
         if inst["address"]:
             inst["address"] = re.sub(r'<[^>]+>', ' ', inst["address"]).strip()
             inst["address"] = re.sub(r'\s+', ' ', inst["address"])
         
         processed.append(inst)

    with_image = sum(1 for i in processed if i.get("image_url"))
    logger.info(
        "Saved %s institutions to %s (%s med image_url, %s uten)",
        len(processed),
        outfile,
        with_image,
        len(processed) - with_image,
    )
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(json.dumps(processed, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
