# Admin-flate: API-handlinger og forventninger

Dette dokumentet beskriver kall fra admin-UI (inkl. lenkede undersider), påkrevd rolle og kjente begrensninger.

## Manuell sjekkliste (nettleser)

1. Logg inn som bruker med rolle **ADMIN**.
2. Åpne utviklerverktøy → **Network**.
3. Gå gjennom admin-hovedsiden og undersider; for hvert API-kall: status **200** (eller forventet 4xx), ikke **404** på `/api/v1/...`.
4. Ved **403**: verifiser rolle i database; ved impersonering skal admin-endepunkter fortsatt bruke ekte admin-konto (se `client.ts` for `/admin` og `/agent/admin`).
5. Ved **timeout** på batch-jobber: forventet ved store datasett; prøv lokalt eller se backend-logg.

## Hovedside `/admin` ([frontend/app/admin/page.tsx](frontend/app/admin/page.tsx))

| Handling | Metode | API-sti under `/api/v1` | Rolle | Merknad |
|----------|--------|---------------------------|-------|---------|
| Batch ekstern risiko | POST | `/agent/admin/batch-risk-update` | ADMIN | Langvarig; kan timeoute i serverless. Impersonering brukes ikke for denne stien (ekte admin identifiseres). |
| Geokoding batch | POST | `/admin/geocoding/batch` | ADMIN | Kartverket/Geonorge; synkron loop. |
| Begrepskatalog scan | POST | `/glossary/scan` | ADMIN | Skanner filer på server. I Docker/Railway er typisk kun `backend/` tilgjengelig; full monorepo-scan som lokalt kan utebli. |
| (Lenke) Risikooversikt | GET | `/risk/prioritized` via `/risk`-side | Innlogget | Se risiko-side. |

## Undersider (`frontend/app/admin/*`)

| Side | API-modul / kall | Rolle (typisk) |
|------|------------------|----------------|
| `logs` | `GET /admin/logs` | ADMIN |
| `financial-analysis` | `GET /admin/financial-analysis/search`, `GET /admin/financial-analysis/property/{id}` | ADMIN |
| `contract-costs` | `GET /admin/contracts/costs` | ADMIN |
| `hms-calendar` | `GET /properties`, `GET /hms/activities/scheduled`, `POST /hms/activities/generate` | Avhenger av endepunkt; kalender er ofte ADMIN |
| `economic-data` | `economicImportApi`, `budgetPredictionApi`, `POST /admin/economic-import/salary-costs` m.fl. | ADMIN |
| `import` | `importApi`, `economicImportApi` | ADMIN |
| `users`, `impersonate` | `userManagementApi` (`/admin/users`…) | ADMIN |
| `procurement` | `procurementApi` | Innlogget / ADMIN etter backend |
| `governance` | `GET /governance/catalog`, `GET /governance/stats`, `POST /governance/catalog/description` | ADMIN for skriveoperasjoner |
| `documents` | `getContracts` | Innlogget |
| `docs` | `GET /help/technical` | Innlogget |
| `ai-lab` | `transparencyApi` | Innlogget |
| `barnevern-*` | `barnevernDocsApi` | Etter backend |

**Systemlogger:** [frontend/app/admin/logs/page.tsx](frontend/app/admin/logs/page.tsx) henter `GET /api/v1/admin/logs`.

## Backend-kilde

- Samlet admin-router: [backend/app/api/v1/admin/__init__.py](backend/app/api/v1/admin/__init__.py) (inkl. `evolution` under `/admin/evolution`).
- Eldre monolittfil `backend/app/api/v1/admin.py` er fjernet (var skygget av `admin/`-pakken og skapte forvirring).

## Manuell verifisering (nettleser)

1. Logg inn som bruker med rolle **ADMIN**.
2. Åpne utviklerverktøy → Network.
3. Trigg hver knapp / side; verifiser HTTP-status **200** (eller forventet 4xx ved tom data), ikke **404** på API-kall.
4. Ved **403**: sjekk rolle i database og at du ikke bruker impersonering som ikke-admin for admin-endepunkter.
5. Ved **timeout** på batch-jobber: vurder kjøring mot lokal backend eller øk timeout i proxy – jobben er synkron på serveren.

## Automatisert røyktest

- **Layout / regresjon (ingen app-import):** `cd backend && python3 scripts/verify_admin_layout.py`
- **Mot kjørende backend (curl):** [scripts/smoke_admin_api.sh](scripts/smoke_admin_api.sh) med `API_BASE_URL`, `BACKEND_SECRET`, `ADMIN_EMAIL`

Full pytest med `tests/conftest.py` laster hele appen og kan være tregt i noen miljøer; layout-sjekken over er ment for raske CI-lokaler.
