# SSB-statistikk i BEFS – teknisk oversikt

Dette dokumentet beskriver **implementasjonen** bak SSB-siden og det kuraterte tabellutvalget. Sluttbrukerveiledning finnes i [BRUKERHJELP.md](BRUKERHJELP.md) under kapittel **SSB Statistikk** og i appen under **Hjelp** → *Ofte stilte spørsmål* → **SSB og statistikk**.

## Frontend

- **Rute:** `frontend/app/ssb/page.tsx` – faner for søk, data, kombinering, rapport.
- **Søk / utvalg:** `frontend/app/components/features/ssb/SSBTableSearch.tsx` – chips for `Hele SSB`, `Kuratert: alle`, `Utdanning`, `Utenforskap / NEET`; synker URL (`?catalog=curated`, `?category=…`).
- **Data og diagram:** `frontend/app/components/features/ssb/SSBDataViewer.tsx` + `SSBJsonStatChart.tsx` – json-stat2, linje/stolpe, valg av akser og dimensjonsfiltre.
- **API-klient:** `frontend/lib/api/ssbApi.ts` – `searchTables(..., { catalog, category })`.

## Backend

- **Live søk:** `GET /api/v1/ssb/tables` uten kuratert modus proxier til PxWebApi v2 (hele Statistikkbanken).
- **Kuratert modus:** Samme endepunkt med `catalog=curated` og/eller `category=<nøkkel>` bruker `app/services/external/ssb_curated_tables.py` og JSON-filen `backend/data/ssb_bufetat_bufdir_tables.json`.
- **Kategorinøkler** (taxonomi): `app/services/external/ssb_table_taxonomy.py` – bl.a. `utdanning`, `utenforskap`, `melding`, `tiltak`, …

## Vedlikehold av kuratert liste

- Bygg/oppdater kortliste: `python backend/scripts/ssb_bufdir_relevant_tables.py` (krever nettverk mot SSB).
- Nye tabeller kan også legges manuelt i `ssb_bufetat_bufdir_tables.json`; kategorier kan utledes automatisk via `classify_ssb_table` eller settes eksplisitt på elementet.

## Relaterte stier

- Metode og kilder (utdanning, NEET, Norge/Sverige): `frontend/app/ssb/utdanning-metode/page.tsx` (`/ssb/utdanning-metode`).
