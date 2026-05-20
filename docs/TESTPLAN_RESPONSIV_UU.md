# Testplan – Responsivitet og universell utforming (BEFS)

## 1. Mål

- Verifisere at hovedlayout (sidebar + hovedinnhold) fungerer på mobil, nettbrett og desktop.
- Fange opp åpenbare brudd på WCAG 2.1 AA som kan avdekkes med enkle manuelle og automatiske tester.

## 2. Omfang

- Frontend-appen på produksjonsmiljø.
- Nøkkelsider:
  - Dashboard (`/dashboard`)
  - Eiendomsside (`/properties/[id]`)
  - Kontraktsside (`/contracts/[id]`)
  - Tilgjengelighetserklæring (`/tilgjengelighet`)
  - Personvern (`/personvern`)

## 3. Responsivitet – manuell test

Test i nettleserens devtools for følgende bredder:

- Mobil: 375×667, 414×896
- Nettbrett: 768×1024
- Desktop: ≥1280px

Sjekkpunkter:

- Sidebar:
  - Skjules på mobil, innhold får full bredde.
  - Vises fast på desktop uten å overlappe hovedinnhold.
- Kort og tabeller:
  - Kort på eiendomssiden bryter til én kolonne på smale skjermer.
  - Tabeller har horisontal scroll ved behov, uten at innhold forsvinner.
- Ingen horisontal scroll på hele siden (med mindre tabell bevisst scroller).

## 4. Tilgjengelighet – manuell test

### Tastaturnavigasjon

- Åpne en side og bruk kun `Tab`/`Shift+Tab`:
  - Skip-lenken «Hopp til hovedinnhold» blir synlig først og fungerer.
  - Alle interaktive elementer (lenker, knapper, input) kan fokuseres i logisk rekkefølge.
  - Fokusindikator er tydelig synlig.

### Skjermleser-smoke

- Start en skjermleser (VoiceOver/NVDA/JAWS) på minst én nøkkelside:
  - Sjekk at hovedoverskrift leses korrekt (H1).
  - Bekreft at knapper med ikoner har meningsfulle `aria-label` der nødvendig.

## 5. Tilgjengelighet – automatiske tester

- Kjør Lighthouse eller axe på nøkkelsidene:
  - Noter WCAG-relaterte funn (kontrast, manglende labels, landmarks).
  - Prioriter funn som gjelder mange komponenter (globale mønstre).

## 6. Regresjon

- Etter layoutendringer:
  - Verifiser at innlogging, navigasjon og roller fortsatt fungerer.
  - Sjekk at chat-widget, modaler og kart fortsatt kan åpnes og lukkes.

