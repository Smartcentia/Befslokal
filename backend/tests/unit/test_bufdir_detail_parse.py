"""Enhetstester for Bufdir detalj-parser."""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2]
_SCRIPTS = _BACKEND / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.bufdir_detail_parse import (  # noqa: E402
    normalize_bufdir_image_url,
    parse_institution_detail_html,
)


def test_normalize_next_image_proxy():
    u = "/_next/image/?url=https%3A%2F%2Fwww.bufdir.no%2Ffoo.jpg&w=1920&q=75"
    assert normalize_bufdir_image_url(u) == "https://www.bufdir.no/foo.jpg"


def test_parse_minimal_institution_html():
    html = """
    <html><body><div class="bd-institution-page">
      <h1 class="bl-size-1">Test institusjon</h1>
      <ul class="bl-carousel__slides"><li>
        <figure class="bl-responsive-image">
          <picture><img src="https://www.bufdir.no/x/a.jpg" alt="hus"/></picture>
          <figcaption class="bl-responsive-image__caption bl-p-t-1"><span>Velkommen</span></figcaption>
          <div class="bl-responsive-image__credit">Foto: A</div>
        </figure>
      </li></ul>
      <ul class="bd-stats-list bd-two-column-list"><li>Statlig</li>
      <li>Kapasitet<!-- -->: <!-- -->4</li></ul>
      <div class="bl-accordion"><h3 class="bl-accordion__header"><div class="bl-accordion__header-content">Kontaktinformasjon</div></h3>
      <div class="bl-accordion__content"><div class="bl-rich-text">
      <p><strong>Postadresse</strong>: Boks 1, 0001 Oslo</p>
      <p>E-post<!-- -->: <a href="mailto:a@b.no">a@b.no</a></p>
      </div></div></div>
    </div></body></html>
    """
    d = parse_institution_detail_html(html, "https://example.invalid/x/")
    assert d.get("parse_error") is None
    assert len(d["gallery"]) == 1
    assert d["gallery"][0]["url"].endswith("/a.jpg")
    assert d["summary"].get("capacity") == 4
    assert d["contact"].get("email") == "a@b.no"


def test_parse_modern_tile_sections_and_link_list():
    """Ny Bufdir-mal uten bd-block-accordion-list (h2 + rik tekst + akkordeon + lenkeliste)."""
    html = """
    <html><body><div class="bd-institution-page">
      <div class="bl-tile bl-typography-small-wrapper">
        <h1 class="bl-size-1">Hovedenhet</h1>
        <p class="bl-size-3 bl-p-b-5">Kort ingress her.</p>
        <h2 class="bl-size-2 bl-p-b-3">Kort om stedet</h2>
        <ul class="bd-stats-list bd-two-column-list"><li>Statlig</li></ul>
        <div class="bl-rich-text bl-m-b-6"><p>Utfyllende <strong>HTML</strong>-tekst.</p></div>
        <div>
          <div class="bl-m-b-4">
            <div class="bl-accordion-list">
              <div class="bl-accordion">
                <div class="bl-accordion__header-content">Mer informasjon</div>
                <div class="bl-accordion__content"><div class="bl-rich-text"><p>Inni accordion.</p></div></div>
              </div>
            </div>
          </div>
          <div class="bd-block-link-list bl-m-b-5">
            <div class="bd-anchor-link"><article class="bl-p-b-4"><h2 class="bl-size-2 bl-p-b-3">Avdelinger</h2></article></div>
            <div class="bd-link-list"><ul class="bl-link-list"><li><a href="https://www.bufdir.no/x/a/">Avd A</a></li></ul></div>
          </div>
        </div>
      </div>
    </div></body></html>
    """
    d = parse_institution_detail_html(html, "https://example.invalid/x/")
    assert d.get("parse_error") is None
    assert len(d["content_sections"]) == 2
    assert d["content_sections"][0]["title"] == "Kort om stedet"
    assert "Utfyllende" in (d["content_sections"][0].get("intro_html") or "")
    assert d["content_sections"][0]["subsections"][0]["title"] == "Mer informasjon"
    assert d["content_sections"][1]["title"] == "Avdelinger"
    assert "Avd A" in (d["content_sections"][1].get("intro_html") or "")


def test_parse_hero_figure_without_carousel():
    """Sider med kun figure.bl-responsive-image (ingen karusell-slides)."""
    html = """
    <html><body><div class="bd-institution-page">
      <div class="bl-tile bl-typography-small-wrapper">
        <h1 class="bl-size-1">Test</h1>
        <figure class="bl-responsive-image">
          <img src="https://www.bufdir.no/contentassets/hero.jpg" alt="Hus" />
          <figcaption class="bl-responsive-image__caption"><span>Ved skogen</span></figcaption>
        </figure>
      </div>
    </div></body></html>
    """
    d = parse_institution_detail_html(html, "https://example.invalid/x/")
    assert d.get("parse_error") is None
    assert len(d["gallery"]) == 1
    assert d["gallery"][0]["url"].endswith("hero.jpg")
    assert d["gallery"][0]["caption"] == "Ved skogen"
