"""
Parser for Bufdir institusjonssider (barnevern/finn-institusjon/<slug>/).
Brukes av scrape_bufdir_institution_pages.py.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

BUFDIR_ORIGIN = "https://www.bufdir.no"


def _inside_bl_carousel(tag: Any) -> bool:
    """True hvis noden ligger inne i Bufdirs karusell (unngå duplikater ved hero-bilde)."""
    return (
        tag.find_parent(
            class_=lambda c: c and any("bl-carousel" in str(x) for x in c)
        )
        is not None
    )


def normalize_bufdir_image_url(src: str | None) -> str:
    if not src or not str(src).strip():
        return ""
    s = str(src).strip()
    if s.startswith("/_next/image"):
        path = s if s.startswith("http") else f"https://www.bufdir.no{s}"
        q = urlparse(path).query
        parsed = parse_qs(q)
        if parsed.get("url") and parsed["url"]:
            return unquote(parsed["url"][0])
    if s.startswith("//"):
        return "https:" + s
    if s.startswith("/"):
        return BUFDIR_ORIGIN.rstrip("/") + s
    return s


def _append_gallery_image(
    gallery: list[dict[str, Any]],
    seen_urls: set[str],
    *,
    url: str,
    caption: str | None,
    credit: str | None,
    alt: str | None,
) -> None:
    if not url or url in seen_urls:
        return
    seen_urls.add(url)
    gallery.append(
        {"url": url, "caption": caption, "credit": credit, "alt": alt}
    )


def _parse_accordion_entries(container: Any) -> list[dict[str, str]]:
    subsections: list[dict[str, str]] = []
    for acc in container.select(".bl-accordion-list .bl-accordion"):
        hbtn = acc.select_one(".bl-accordion__header-content")
        sub_title = hbtn.get_text(strip=True) if hbtn else ""
        body = acc.select_one(".bl-accordion__content .bl-rich-text")
        body_html = body.decode_contents() if body else ""
        if sub_title:
            subsections.append({"title": sub_title, "body_html": body_html})
    return subsections


def _parse_modern_tile_content_sections(tile: Any) -> list[dict[str, Any]]:
    """
    Nyere Bufdir-mal: innhold ligger i bl-tile uten bd-block-accordion-list > section.
    """
    sections: list[dict[str, Any]] = []
    h2_main = tile.select_one(":scope > h2.bl-size-2")
    if h2_main:
        entry: dict[str, Any] = {
            "title": h2_main.get_text(" ", strip=True),
            "intro_html": None,
            "subsections": [],
        }
        for sib in h2_main.find_next_siblings():
            if not getattr(sib, "name", None):
                continue
            cls = sib.get("class") or []
            if sib.name == "ul" and "bd-stats-list" in cls:
                continue
            if sib.name == "div" and "bl-rich-text" in cls:
                entry["intro_html"] = sib.decode_contents()
                continue
            if sib.name == "div" and not cls and sib.select_one(".bl-accordion-list"):
                entry["subsections"].extend(_parse_accordion_entries(sib))
        if entry["intro_html"] or entry["subsections"] or entry["title"]:
            sections.append(entry)

    for block in tile.select("div.bd-block-link-list"):
        h2 = block.select_one("h2.bl-size-2")
        if not h2:
            continue
        link_root = block.select_one("div.bd-link-list") or block
        sections.append(
            {
                "title": h2.get_text(" ", strip=True),
                "intro_html": link_root.decode_contents(),
                "subsections": [],
            }
        )
    return sections


def parse_institution_detail_html(html: str, source_url: str) -> dict[str, Any]:
    """
    Returnerer dict med gallery, summary, contact, content_sections, m.m.
    Ved feil: parse_error satt, andre felt kan mangle.
    """
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("div.bd-institution-page")
    if not root:
        return {
            "source_detail_url": source_url,
            "parse_error": "missing_bd-institution-page",
            "gallery": [],
            "summary": {},
            "contact": {},
            "content_sections": [],
        }

    h1 = root.select_one("h1.bl-size-1")
    h1_title = h1.get_text(strip=True) if h1 else None

    intro_text = None
    if h1:
        for sib in h1.find_next_siblings():
            if sib.name == "p" and sib.get("class") and "bl-size-3" in sib.get("class"):
                intro_text = sib.get_text(" ", strip=True)
                break

    gallery: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for li in root.select("ul.bl-carousel__slides > li"):
        img = li.select_one("img")
        if not img:
            continue
        raw = img.get("src") or ""
        url = normalize_bufdir_image_url(raw)
        cap_spans = li.select("figcaption span")
        caption = None
        if cap_spans:
            caption = cap_spans[0].get_text(strip=True) or None
        cred_el = li.select_one(".bl-responsive-image__credit")
        credit = cred_el.get_text(strip=True) if cred_el else None
        alt = (img.get("alt") or "").strip() or None
        _append_gallery_image(
            gallery, seen_urls, url=url, caption=caption, credit=credit, alt=alt
        )

    # Enkeltsider uten karusell, kun hero-figure.bl-responsive-image
    for fig in root.select("figure.bl-responsive-image"):
        if _inside_bl_carousel(fig):
            continue
        img = fig.select_one("img")
        if not img:
            continue
        raw = img.get("src") or ""
        url = normalize_bufdir_image_url(raw)
        cap_spans = fig.select("figcaption span")
        caption = cap_spans[0].get_text(strip=True) if cap_spans else None
        cred_el = fig.select_one(".bl-responsive-image__credit")
        credit = cred_el.get_text(strip=True) if cred_el else None
        alt = (img.get("alt") or "").strip() or None
        _append_gallery_image(
            gallery, seen_urls, url=url, caption=caption, credit=credit, alt=alt
        )

    summary: dict[str, Any] = {
        "raw_bullets": [],
        "ownership": None,
        "placement_type": None,
        "capacity": None,
        "place": None,
    }
    for li in root.select("ul.bd-stats-list li"):
        text = li.get_text(" ", strip=True)
        if not text:
            continue
        summary["raw_bullets"].append(text)
        if re.match(r"^Kapasitet\s*:", text, re.I):
            m = re.search(r"(\d+)", text)
            if m:
                summary["capacity"] = int(m.group(1))
        elif re.match(r"^Plasseringstype\s*:", text, re.I):
            summary["placement_type"] = re.sub(
                r"^Plasseringstype\s*:\s*", "", text, flags=re.I
            ).strip()
        elif re.match(r"^Sted\s*:", text, re.I):
            summary["place"] = re.sub(r"^Sted\s*:\s*", "", text, flags=re.I).strip()
        else:
            summary["ownership"] = text

    contact: dict[str, Any] = {
        "postal_address": None,
        "email": None,
        "phone": None,
        "rich_html": None,
    }
    for acc in root.select("div.bl-accordion"):
        hdr = acc.select_one(".bl-accordion__header-content")
        if not hdr or "Kontaktinformasjon" not in hdr.get_text():
            continue
        content = acc.select_one(".bl-accordion__content .bl-rich-text")
        if content:
            contact["rich_html"] = content.decode_contents()
            for a in content.select('a[href^="mailto:"]'):
                href = a.get("href") or ""
                contact["email"] = href.replace("mailto:", "").split("?")[0].strip()
            for a in content.select('a[href^="tel:"]'):
                contact["phone"] = re.sub(
                    r"^tel:", "", a.get("href") or "", flags=re.I
                ).strip()
            for p in content.select("p"):
                t = p.get_text(" ", strip=True)
                if re.match(r"^Postadresse\s*:", t, re.I):
                    contact["postal_address"] = re.sub(
                        r"^Postadresse\s*:\s*", "", t, flags=re.I
                    ).strip()
                    break
        break

    content_sections: list[dict[str, Any]] = []
    for sec in root.select("div.bd-block-accordion-list > section"):
        h2 = sec.find("h2", class_=lambda c: c and "bl-size-2" in c)
        if not h2:
            continue
        title = h2.get_text(strip=True)
        if not title:
            continue
        entry: dict[str, Any] = {
            "title": title,
            "intro_html": None,
            "subsections": [],
        }
        for child in sec.find_all(recursive=False):
            if child.name != "div":
                continue
            cls = child.get("class") or []
            if "bd-block-rich-text" in cls and "bl-accordion-list" not in cls:
                rt = child.select_one(".bl-rich-text")
                if rt:
                    entry["intro_html"] = rt.decode_contents()
        for acc in sec.select(".bl-accordion-list .bl-accordion"):
            hbtn = acc.select_one(".bl-accordion__header-content")
            sub_title = hbtn.get_text(strip=True) if hbtn else ""
            body = acc.select_one(".bl-accordion__content .bl-rich-text")
            body_html = body.decode_contents() if body else ""
            if sub_title:
                entry["subsections"].append(
                    {"title": sub_title, "body_html": body_html}
                )
        content_sections.append(entry)

    if not content_sections:
        tile = root.select_one("div.bl-tile.bl-typography-small-wrapper")
        if tile:
            content_sections = _parse_modern_tile_content_sections(tile)

    return {
        "source_detail_url": source_url,
        "parse_error": None,
        "h1_title": h1_title,
        "intro_text": intro_text,
        "gallery": gallery,
        "summary": summary,
        "contact": contact,
        "content_sections": content_sections,
    }
