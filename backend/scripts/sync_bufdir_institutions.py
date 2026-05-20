#!/usr/bin/env python3
"""
Hent barnevernsinstitusjoner fra Bufdir «Finn institusjon» og valgfritt match mot BEFS properties.

Teknisk (2026-04):
- Next.js-listen pagineres med ?page=N der siste side inneholder alle kort kumulativt (20 per steg).
- Ingen offentlig JSON-API funnet; data parses fra HTML (BeautifulSoup).
- Stabile lenker: /barnevern/finn-institusjon/<slug>/ (der de finnes) og numerisk id på <a>.

Kjør fra backend/ med venv:
  python3 scripts/sync_bufdir_institutions.py --out-dir data/bufdir_institutions
  python3 scripts/sync_bufdir_institutions.py --eierform statlig --match-befs
  python3 scripts/sync_bufdir_institutions.py --dry-run  # kun hent/parse, ingen filer

Ved --match-befs skrives også gap_not_in_befs.json, gap_befs_not_in_bufdir.json og
match_duplicate_property_ids.json (sammen med bufdir_institutions.* og supplementary_sitemap.json).

Miljø for --match-befs: DATABASE_URL (eller .env i backend/).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from collections import Counter
from typing import Any
from xml.etree import ElementTree as ET

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_BACKEND_ROOT / ".env")
except Exception:
    pass

from bs4 import BeautifulSoup
from bs4.element import Tag

LIST_URL = "https://www.bufdir.no/barnevern/finn-institusjon/"
SITEMAP_URL = "https://www.bufdir.no/sitemap.xml"
USER_AGENT = "BEFS-BufdirSync/1.0 (+https://github.com/)"

EIERFORM_QUERY = {
    "alle": "",
    "statlig": "institutionOwnerShipType=1",
    "privat": "institutionOwnerShipType=2",
    "ideell": "institutionOwnerShipType=3",
    "kommunal": "institutionOwnerShipType=4",
}


@dataclass
class BufdirInstitution:
    name: str
    eierform: str | None
    plasseringstyper: str | None
    kapasitet: str | None
    sted: str | None
    detail_url: str | None
    link_element_id: str | None
    besoksadresse: str | None
    postadresse: str | None
    telefon: str | None
    epost: str | None
    match_property_id: str | None = None
    match_method: str | None = None


def _http_get(url: str, timeout: int = 60) -> str:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _listing_url(eierform_key: str, page: int) -> str:
    base = LIST_URL.rstrip("/") + "/"
    parts: list[str] = []
    q = EIERFORM_QUERY.get((eierform_key or "alle").lower().strip())
    if q is None:
        raise SystemExit(f"Ukjent eierform. Velg: {', '.join(EIERFORM_QUERY)}")
    if q:
        parts.append(q)
    if page > 1:
        parts.append(f"page={page}")
    if not parts:
        return base
    return base + "?" + "&".join(parts)


def _total_treff(html: str) -> int:
    m = re.search(r"totalt[^0-9]*(\d+)[^0-9]*treff", html, re.I)
    if not m:
        raise RuntimeError("Fant ikke 'totalt N treff' i HTML (layout endret?)")
    return int(m.group(1))


def fetch_listing_html(eierform: str, delay_s: float) -> str:
    first = _listing_url(eierform, 1)
    html = _http_get(first)
    total = _total_treff(html)
    pages = max(1, (total + 19) // 20)
    if pages == 1:
        return html
    last_url = _listing_url(eierform, pages)
    time.sleep(delay_s)
    return _http_get(last_url)


def _parse_visiting_line(line: str | None) -> tuple[str | None, str | None, str | None]:
    if not line:
        return None, None, None
    s = re.sub(r"\s+", " ", line.strip())
    m = re.match(r"^(.+?),\s*(\d{4})\s+(.+)$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    return s, None, None


def _rich_text_addresses(acc: Tag) -> tuple[str | None, str | None]:
    besok: str | None = None
    post: str | None = None
    for h4 in acc.find_all("h4"):
        label = h4.get_text(strip=True).lower()
        nxt = h4.find_next_sibling("p")
        if not nxt:
            continue
        val = nxt.get_text(" ", strip=True)
        if "besøk" in label:
            besok = val or besok
        elif "post" in label:
            post = val or post
    if not besok:
        first_p = acc.find("p")
        if first_p and not first_p.find_previous("h4"):
            t = first_p.get_text(" ", strip=True)
            if t and "Postadresse" not in t:
                besok = t
    return besok, post


def parse_institution_cards(html: str) -> list[BufdirInstitution]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[BufdirInstitution] = []
    for card in soup.select(".bd-child-services-institution-card"):
        h3 = card.select_one("h3.bd-child-services-institution-card__title")
        name = h3.get_text(strip=True) if h3 else ""
        a = h3.select_one("a") if h3 else None
        detail_url = a.get("href") if a and a.has_attr("href") else None
        link_id = a.get("id") if a and a.has_attr("id") else None

        stats_ps = card.select(".bd-child-services-institution-card__stats p")
        eierform = plassering = kapasitet = sted = None
        for p in stats_ps:
            text = p.get_text(" ", strip=True)
            if not text:
                continue
            if text.startswith("Plasseringstype"):
                plassering = text.split(":", 1)[-1].strip()
            elif text.startswith("Kapasitet"):
                kapasitet = text.split(":", 1)[-1].strip()
            elif text.startswith("Sted"):
                sted = text.split(":", 1)[-1].strip()
            elif text in ("Statlig", "Privat", "Ideell", "Kommunal"):
                eierform = text

        besok: str | None = None
        post: str | None = None
        phone: str | None = None
        email: str | None = None

        acc = card.select_one(".bl-accordion__content .bl-rich-text")
        if acc:
            besok, post = _rich_text_addresses(acc)

        for tel_a in card.select('a[href^="tel:"]'):
            phone = tel_a.get_text(strip=True) or phone
        for mail_a in card.select('a[href^="mailto:"]'):
            raw = (mail_a.get("href") or "").replace("mailto:", "")
            email = raw.split("?")[0].strip() or email

        out.append(
            BufdirInstitution(
                name=name,
                eierform=eierform,
                plasseringstyper=plassering,
                kapasitet=kapasitet,
                sted=sted,
                detail_url=detail_url,
                link_element_id=str(link_id) if link_id else None,
                besoksadresse=besok,
                postadresse=post,
                telefon=phone,
                epost=email,
            )
        )
    return out


def collect_supplementary_sitemap_urls() -> dict[str, Any]:
    xml = _http_get(SITEMAP_URL)
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text for el in root.findall(".//sm:loc", ns) if el is not None and el.text]
    finn = sorted(
        {
            u
            for u in locs
            if "/barnevern/finn-institusjon/" in u and u.rstrip("/").split("/")[-1] != "finn-institusjon"
        }
    )
    kontakt = sorted({u for u in locs if "/om/kontakt" in u.lower() or "/kontakt/" in u.lower()})
    return {
        "finn_institusjon_detail_pages": finn,
        "kontakt_related": kontakt[:50],
        "note": (
            "Begrensninger: Om/Kontakt gir organisasjon og regionkontor, ikke full eiendomsliste. "
            "Institusjonsdata kommer fra listing (paginert HTML). Sitemap har typisk færre "
            "finn-institusjon-URL-er enn antall treff fordi noen kun lenker til ekstern nettside. "
            "Familievern/fosterhjem dekkes ikke av dette registeret."
        ),
    }


def write_outputs(rows: list[BufdirInstitution], out_dir: Path, supplementary: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = [asdict(r) for r in rows]
    (out_dir / "bufdir_institutions.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    fields = list(asdict(rows[0]).keys()) if rows else []
    if fields:
        with (out_dir / "bufdir_institutions.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow(asdict(r))
    (out_dir / "supplementary_sitemap.json").write_text(
        json.dumps(supplementary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def match_against_befs(rows: list[BufdirInstitution]) -> list[Any]:
    from sqlalchemy import select

    import app.db.base  # noqa: F401
    import app.domains.core.models.center  # noqa: F401
    import app.domains.hms.models.internal_control  # noqa: F401
    import app.domains.hms.models.risk  # noqa: F401
    from app.db.session import SessionLocal
    from app.domains.core.models.property import Property
    from app.domains.core.utils.property_matcher import build_property_index, match_property

    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("DATABASE_URL mangler for --match-befs")

    try:
        async with SessionLocal() as session:
            res = await session.execute(select(Property))
            props = list(res.scalars().all())
    except OSError as e:
        raise SystemExit(
            f"Kunne ikke koble til database (sjekk DATABASE_URL / nettverk): {e}"
        ) from e
    except Exception as e:
        raise SystemExit(f"Database-feil ved lasting av properties: {e}") from e

    idx = build_property_index(props)

    for r in rows:
        addr, postnr, city = _parse_visiting_line(r.besoksadresse)
        prop, method = match_property(
            idx,
            address=addr,
            postal_code=postnr,
            city=city,
            name=r.name,
        )
        if prop is not None:
            r.match_property_id = str(prop.property_id)
            r.match_method = method
    return props


def _property_gap_row(p: Any) -> dict[str, Any]:
    return {
        "property_id": str(p.property_id),
        "name": p.name,
        "address": p.address,
        "postal_code": p.postal_code,
        "city": p.city,
        "region": p.region,
        "unit_type_derived": p.unit_type_derived,
        "lokalisering_id": p.lokalisering_id,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Synk Bufdir barnevernsinstitusjoner → JSON/CSV (+ valgfri BEFS-match)")
    ap.add_argument("--out-dir", type=Path, default=Path("data/bufdir_institutions"), help="Mappe for utdata")
    ap.add_argument(
        "--eierform",
        choices=list(EIERFORM_QUERY.keys()),
        default="alle",
        help="Filtrer listing (Bufdir query institutionOwnerShipType)",
    )
    ap.add_argument("--delay", type=float, default=0.6, help="Sekunder mellom HTTP-kall")
    ap.add_argument("--match-befs", action="store_true", help="Match mot properties via DATABASE_URL")
    ap.add_argument("--skip-sitemap-extra", action="store_true", help="Ikke hent sitemap (supplementary_sitemap.json)")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Hent og parse, men ikke skriv JSON/CSV/gap-filer (kun stderr-oppsummering)",
    )
    args = ap.parse_args()

    os.chdir(_BACKEND_ROOT)

    print(f"Henter listing (eierform={args.eierform}) …", file=sys.stderr)
    html = fetch_listing_html(args.eierform, delay_s=args.delay)
    rows = parse_institution_cards(html)
    total = _total_treff(html)
    print(f"Parsert {len(rows)} kort (rapportert treff: {total})", file=sys.stderr)
    if len(rows) != total:
        print("ADVARSEL: antall kort matcher ikke totalt — sjekk layout.", file=sys.stderr)

    supplementary: dict[str, Any] = {"skipped": True}
    if not args.skip_sitemap_extra:
        time.sleep(args.delay)
        print("Henter sitemap-supplement …", file=sys.stderr)
        supplementary = collect_supplementary_sitemap_urls()

    props_for_gap: list[Any] = []
    if args.match_befs:
        print("Matcher mot BEFS properties …", file=sys.stderr)
        props_for_gap = asyncio.run(match_against_befs(rows))

    if args.dry_run:
        print(f"[dry-run] {len(rows)} institusjoner, eierform={args.eierform}", file=sys.stderr)
        if args.match_befs:
            matched = sum(1 for r in rows if r.match_property_id)
            print(f"[dry-run] Match: {matched}/{len(rows)}", file=sys.stderr)
        return 0

    write_outputs(rows, args.out_dir, supplementary)

    if args.match_befs:
        matched = sum(1 for r in rows if r.match_property_id)
        print(f"Match: {matched}/{len(rows)}", file=sys.stderr)
        gap = [r for r in rows if not r.match_property_id]
        gap_path = args.out_dir / "gap_not_in_befs.json"
        gap_path.write_text(json.dumps([asdict(r) for r in gap], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Skrev {gap_path} ({len(gap)} uten treff)", file=sys.stderr)

        matched_ids = {r.match_property_id for r in rows if r.match_property_id}
        bef_gap = [p for p in props_for_gap if str(p.property_id) not in matched_ids]
        bef_path = args.out_dir / "gap_befs_not_in_bufdir.json"
        bef_path.write_text(
            json.dumps([_property_gap_row(p) for p in bef_gap], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Skrev {bef_path} ({len(bef_gap)} properties uten Bufdir-treff)", file=sys.stderr)

        cnt = Counter(r.match_property_id for r in rows if r.match_property_id)
        dups = {pid: n for pid, n in cnt.items() if n > 1}
        dup_path = args.out_dir / "match_duplicate_property_ids.json"
        dup_payload = {
            "note": "Flere Bufdir-kort pekte på samme property_id — manuell gjennomgang.",
            "counts": dups,
            "institutions": [
                asdict(r)
                for r in rows
                if r.match_property_id and dups.get(r.match_property_id)
            ],
        }
        dup_path.write_text(json.dumps(dup_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Skrev {dup_path} ({len(dups)} property_id med duplikat-treff)", file=sys.stderr)

    print(f"Skrev {args.out_dir}/bufdir_institutions.json og .csv", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
