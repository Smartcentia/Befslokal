# GL og husleie per år (2020–2026)

_Generert: 2026-04-12 21:33 UTC_

Grunnlag: `gl_transactions` med `property_id` **eller** `dim1_kode` via `koststed_mapping` (samme kjerne som `GET /properties/{id}/gl-costs`). Husleie: kontonavn i LEASE-settet eller `ILIKE 'Leie %'`.

## Sammendrag

- Eiendommer totalt: **642**
- Minst ett år med GL (>0): **192**
- Alle år **2020–2026** med GL-total >0: **0**
- Alle år med husleie-posteringer >0: **0**
- Alle år med **både** total og husleie: **0**

### Eiendommer med data per kalenderår (antall)

| År | Med GL (total>0) | Med husleie | Med begge |
|---|---:|---:|---:|
| 2020 | 133 | 129 | 129 |
| 2021 | 144 | 131 | 131 |
| 2022 | 148 | 140 | 140 |
| 2023 | 148 | 119 | 119 |
| 2024 | 158 | 126 | 126 |
| 2025 | 171 | 130 | 130 |
| 2026 | 0 | 0 | 0 |

## Årsvelger i frontend (`/properties/[id]`)

Dropdown **«Kostnadssjekk per år»** fylles kun med `available_years` fra `getGLCosts` — dvs. **år som faktisk har GL-rader** for eiendommen (property_id + koststed_mapping), **ikke** en fast liste 2020–2026.
Mangler det regnskapsdata for et år, vises ikke det året i listen (kan bli «Ingen år»).

Full detalj: `property_gl_year_matrix_2020_2026.csv`
