# Neste steg — BEFS eiendomsportefølje

Oppsummering av hva som er gjort og hva som gjenstår.

## Fullført (siste sesjon — 2026-05-09)

### Nye DB-kolonner i `properties`-tabellen

Alle kolonner er lagt til via Alembic-migrasjoner, populert med scripts og committet + deployet:

| Kolonne | Type | Kilde | Dekningsgrad |
|---------|------|-------|--------------|
| `gl_rent_2025` | NUMERIC(14,2) | GL-regnskap 2025 (srs_kategori='Lokaler') | ~145 eiendommer, ~430 MNOK |
| `lok_omrade` | VARCHAR(50) | Eiendomsportefølje-CSV | ~213 eiendommer |
| `lok_distrikt` | VARCHAR(50) | Eiendomsportefølje-CSV | ~213 eiendommer |
| `fylke` | VARCHAR(50) | Eiendomsportefølje-CSV / Eiendomsoversikt-CSV | ~213 eiendommer |
| `leased_area_kvm` | NUMERIC(10,1) | Eiendomsoversikt-CSV | ~181 eiendommer |
| `elements_id` | VARCHAR(200) | Eiendomsoversikt-CSV | ~207 eiendommer |
| `utleier_kategori` | SMALLINT | Eiendomsoversikt-CSV (1=privat, 2=offentlig) | ~213 eiendommer |
| `egnethet_lokalisering` | VARCHAR(100) | Eiendomsportefølje-CSV | ~213 eiendommer |
| `egnethet_bygg` | VARCHAR(100) | Eiendomsportefølje-CSV | ~213 eiendommer |
| `prioritert_videroforing` | VARCHAR(50) | Eiendomsportefølje-CSV | ~213 eiendommer |
| `ar_videreutvikling` | INTEGER | Eiendomsportefølje-CSV | ~213 eiendommer |
| `kostnader_videreutvikling` | NUMERIC(14,2) | Eiendomsportefølje-CSV | ~213 eiendommer |
| `malgruppe` | VARCHAR | Oversikt bygg og eiendom-CSV | tidligere sesjon |
| `contract_rent_nok` | NUMERIC(14,2) | Oversikt bygg og eiendom-CSV | ~181 eiendommer, ~319 MNOK |
| `contract_maint_nok` | NUMERIC(14,2) | Oversikt bygg og eiendom-CSV | tidligere sesjon |
| `contract_common_nok` | NUMERIC(14,2) | Oversikt bygg og eiendom-CSV | tidligere sesjon |
| `contract_user_ops_nok` | NUMERIC(14,2) | Oversikt bygg og eiendom-CSV | tidligere sesjon |
| `extension_terms` | VARCHAR | Oversikt bygg og eiendom-CSV | tidligere sesjon |
| `price_adj_clause` | VARCHAR | Oversikt bygg og eiendom-CSV | tidligere sesjon |

**KRITISK arkitekturpoeng – to separate husleie-kilder:**
- `contract_rent_nok` = avtalefestet husleie fra leieavtale (~319 MNOK)
- `gl_rent_2025` = faktisk bokført husleie fra GL-regnskap 2025 (~430 MNOK)
- Disse overskrives ALDRI av hverandre

### Enrich-scripts

- `backend/scripts/enrich_portefolje.py` — beriker fra Eiendomsportefølje-CSV (213 eiendommer)
- `backend/scripts/enrich_eiendomsoversikt.py` — beriker fra Eiendomsoversikt-CSV (204 eiendommer)

### CI/CD

- `.github/workflows/smoke.yml` — Playwright smoke på Vercel deploy
- `frontend/e2e/smoke.spec.ts` og `navigation.spec.ts` — 9 tester, alle grønne

---

## Neste steg

### 1. Eksponere nye felt i frontend (Prioritet: HØY)

Eiendomsdetaljsiden (`/properties/[id]`) viser ikke de nye feltene. Legg til:

- **Husleie-panel med to kilder:** vis både `contract_rent_nok` (avtalefestet) og `gl_rent_2025` (GL-bokført) med tydelig merking av kilde og differanse.
- **Porteføljedata:** `lok_omrade`, `lok_distrikt`, `fylke`, `leased_area_kvm`, `elements_id`, `utleier_kategori`.
- **Egnethet:** `egnethet_lokalisering` og `egnethet_bygg` med fargeindikator (1=rød, 2=oransje, 3=gul, 4=grønn).
- **Videreutvikling:** `prioritert_videroforing`, `ar_videreutvikling`, `kostnader_videreutvikling`.

### 2. KI-Kollega / Text-to-SQL (Prioritet: HØY)

SCHEMA.md er oppdatert med de nye feltene. Verifiser at KI-Kollega kan svare riktig på:
- «Hva er faktisk husleie vs avtalefestet leie for [eiendom]?»
- «Hvilke eiendommer i Trøndelag (lok_omrade) har egnethet bygg under 3?»
- «Hvilke eiendommer er eid av private utleiere (utleier_kategori=1)?»

### 3. Oversikt/dashboard-visning (Prioritet: MIDDELS)

- Legg til kolonne `gl_rent_2025` og `contract_rent_nok` i `/oversikt` full porteføljeliste.
- Vurder å vise differanse (GL vs kontrakt) som indikator på prisavvik.

### 4. Agresso-import av husleie (Prioritet: MIDDELS)

`gl_rent_2025` er for øyeblikket et statisk snapshot fra 2025. Vurder:
- Automatisk oppdatering fra GL-import (ny kolonne `gl_rent_<ar>` per år, eller dynamisk fra `gl_transactions`).
- Alternativt: bruk `gl_transactions WHERE srs_kategori='Lokaler' AND ar=2025` direkte i rapporter.

### 5. Egnethetskart (Prioritet: LAV)

Visualiser `egnethet_lokalisering` og `egnethet_bygg` på kartet (fargekoding per eiendom). Kart-komponenten støtter allerede markør-farger.

### 6. Datakvalitet – gjenstående hull

Kjør `SELECT COUNT(*) FROM properties WHERE gl_rent_2025 IS NULL AND contract_rent_nok IS NULL` for å finne eiendommer uten noen husleiekilde. Disse bør prioriteres for manuell innlegging eller GL-kobling.

---

## Teknisk gjeld / kjente issues

- `OVERSIKT_BYGG_EIENDOM_CSV.md` dokumenterte at egnethet_*, prioritert_videroforing, ar_videreutvikling og kostnader_videreutvikling ble lagret i `external_data` — de er nå egne kolonner. Scriptet `import_oversikt_bygg_eiendom_csv.py` bør oppdateres til å skrive til de nye kolonnene i stedet for `external_data`.
- `enrich_portefolje.py` og `enrich_eiendomsoversikt.py` bør kjøres på nytt mot produksjons-DB etter neste CSV-eksport fra Elements.
