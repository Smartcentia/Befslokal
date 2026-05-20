#!/usr/bin/env python3
"""
Hent alle familievernkontorer fra bufdir.no (liste + detaljsider).

Detaljsidene har ofte det formelle navnet (f.eks. «Familievernkontoret i …»)
selv om oversiktslenken bare viser sted/kommune. Skriptet lagrer strukturert JSON.

Kjør fra repo:
  cd backend && python3 scripts/scrape_familievernkontor_bufdir.py

Utdata: backend/data/familievernkontor_bufdir.json
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

BACKEND = Path(__file__).resolve().parent.parent
OUT_FILE = BACKEND / "data" / "familievernkontor_bufdir.json"
INDEX_URL = "https://www.bufdir.no/familie/familievernkontorer/"
USER_AGENT = "BEFS-FamilievernScraper/1.0 (+https://github.com/)"

OFFICE_URL_RE = re.compile(
    r"^https://www\.bufdir\.no/familie/familievernkontorer/oversikt/([^/]+)/$"
)


def _fetch(client: httpx.Client, url: str) -> str:
    r = client.get(url, follow_redirects=True, timeout=45.0)
    r.raise_for_status()
    return r.text


def parse_index(html: str) -> tuple[dict[str, str], dict[str, str]]:
    """slug -> region label, slug -> rå lenketekst fra oversikten."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if not main:
        return {}, {}

    regions: dict[str, str] = {}
    labels: dict[str, str] = {}
    current_region: str | None = None

    for tag in main.find_all(["h2", "a"]):
        if tag.name == "h2":
            t = tag.get_text(strip=True)
            if t.startswith("Region "):
                current_region = t
        elif tag.name == "a" and tag.get("href"):
            m = OFFICE_URL_RE.match(tag["href"].strip())
            if m and current_region:
                slug = m.group(1)
                regions[slug] = current_region
                labels[slug] = tag.get_text(strip=True)

    return regions, labels


def _uniq_preserve(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def parse_office_page(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    meta_desc = None
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md["content"].strip()

    title_el = soup.find("title")
    document_title = title_el.get_text(strip=True) if title_el else None

    container = soup.select_one("div.bd-family-services-office-page")
    if not container:
        container = soup.find("main")

    h1_el = container.find("h1") if container else None
    official_name = h1_el.get_text(strip=True) if h1_el else None

    phones: list[str] = []
    emails: list[str] = []
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if h.lower().startswith("tel:"):
            txt = a.get_text(strip=True)
            num = txt or re.sub(r"^tel:\s*", "", h, flags=re.I).strip()
            if num:
                phones.append(num)
        elif h.lower().startswith("mailto:"):
            addr = h.split(":", 1)[1].split("?")[0]
            if addr:
                emails.append(addr)

    phones = _uniq_preserve(phones)
    emails = _uniq_preserve(emails)

    intro_parts: list[str] = []
    intro_block = None
    if container:
        intro_block = container.select_one(
            ".bd-super-special-content-case-for-family-sevice-office-page-main-intro-field .bl-rich-text"
        )
    if intro_block:
        intro_parts.append(intro_block.get_text("\n", strip=True))

    first_phone_p = None
    if container:
        for p in container.find_all("p", class_=re.compile(r"bl-size-3")):
            if p.find("a", href=re.compile(r"^tel:", re.I)):
                first_phone_p = p.get_text(" ", strip=True)
                break
    if first_phone_p:
        intro_parts.append(first_phone_p)

    accordion_sections: list[dict[str, str]] = []
    if container:
        for acc in container.select(".bl-accordion"):
            header = acc.select_one(".bl-accordion__header-content")
            content = acc.select_one(".bl-accordion__content")
            sec_title = header.get_text(strip=True) if header else ""
            texts: list[str] = []
            if content:
                for rt in content.select(".bl-rich-text"):
                    t = rt.get_text("\n", strip=True)
                    if t:
                        texts.append(t)
            accordion_sections.append(
                {"title": sec_title, "text": "\n\n".join(texts)}
            )

    course_links: list[dict[str, str]] = []
    if container:
        for a in container.find_all("a", href=True):
            href = a["href"]
            if "/familie/familievernkontorer/oversikt/" in href and "/kurs/" in href:
                course_links.append(
                    {"title": a.get_text(strip=True), "url": href.strip()}
                )

    full_text = ""
    if container:
        full_text = container.get_text("\n", strip=True)

    return {
        "url": url,
        "document_title": document_title,
        "meta_description": meta_desc,
        "official_name": official_name,
        "phones": phones,
        "emails": emails,
        "intro_and_summary": "\n\n".join(intro_parts) if intro_parts else None,
        "accordion_sections": accordion_sections,
        "course_links": course_links,
        "full_text": full_text,
    }


def _slug_from_url(url: str) -> str | None:
    path = urlparse(url).path.strip("/").split("/")
    if len(path) >= 2 and path[-2] == "oversikt":
        return path[-1]
    return None


def run(delay: float, dry_run: bool) -> None:
    out: dict[str, Any] = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source_index": INDEX_URL,
        "offices": [],
    }

    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
        index_html = _fetch(client, INDEX_URL)
        regions, list_labels = parse_index(index_html)
        slugs = sorted(regions.keys())

        if dry_run:
            print(f"Tørrkjøring: {len(slugs)} kontorer funnet.")
            for s in slugs[:5]:
                print(f"  - {s}: {regions[s]}")
            return

        for i, slug in enumerate(slugs):
            url = f"https://www.bufdir.no/familie/familievernkontorer/oversikt/{slug}/"
            try:
                html = _fetch(client, url)
                detail = parse_office_page(html, url)
            except Exception as e:
                detail = {
                    "url": url,
                    "error": str(e),
                    "official_name": None,
                }

            office: dict[str, Any] = {
                "slug": slug,
                "region": regions.get(slug),
                "list_page_link_text": list_labels.get(slug),
            }
            office.update(detail)
            out["offices"].append(office)

            if i < len(slugs) - 1 and delay > 0:
                time.sleep(delay)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Skrev {len(out['offices'])} kontorer til {OUT_FILE}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Bufdir familievernkontorer")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="Sekunder mellom HTTP-kall (standard 0.35)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Bare les indeks, ikke detaljsider",
    )
    args = parser.parse_args()
    run(delay=args.delay, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
