# BEFS – Komplett testguide

Denne guiden beskriver hvordan du tester hele løsningen – både fra brukerperspektiv (E2E, manuelle tester) og fra logikk/kode-perspektiv (unit, integrasjon, API).

---

## 1. Oversikt over testlag

| Lag | Verktøy | Formål |
|-----|---------|--------|
| **Unit** | pytest, Vitest | Isolerte tester for funksjoner, komponenter, modeller |
| **Integrasjon** | pytest | API + DB, eksterne tjenester (mocket eller ekte) |
| **E2E / Bruker** | Playwright | Full flyt i nettleser mot produksjon eller lokal |
| **Manuell** | Sjekkliste | Responsivitet, tilgjengelighet, regresjon |

---

## 2. Backend – logikk og kode

### 2.1 Rask kjøring (unit-tester)

```bash
cd backend
make test
```

Kjører kun `tests/unit/` (rask, isolert). Perfekt for CI og hurtig validering.

### 2.2 Med coverage

```bash
cd backend
make test-cov
```

Viser hvilke linjer som mangler testdekning.

### 2.3 Alle backend-tester

```bash
cd backend
source .venv/bin/activate
PYTHONWARNINGS=ignore pytest tests/ -v
```

**Merk:** Noen tester krever:
- `DATABASE_URL` (PostgreSQL) for integrasjonstester
- `OPENAI_API_KEY` for KI Kollega golden set
- Eksterne API-er (NVE, Frost, SSB m.m.) – disse mockes ofte

### 2.4 Selektiv kjøring med markører

```bash
# Kun unit-tester
pytest tests/ -m unit -v

# Kun API-tester
pytest tests/ -m api -v

# Ekskluder trege tester
pytest tests/ -m "not slow" -v

# Kun integrasjon (krever DB)
pytest tests/ -m integration -v
```

### 2.5 KI Kollega-spesifikke tester

```bash
# Comprehensive (ingen LLM/DB)
pytest tests/test_ki_kollega_comprehensive.py tests/integration/test_ki_kollega_integration.py -v

# Golden set (krever DSPy cache skrivbar, ev. DB)
pytest tests/test_ki_kollega_golden_set.py -v
```

### 2.6 Backend teststruktur

| Kategori | Eksempler |
|----------|-----------|
| Unit | `tests/unit/test_models.py`, `tests/test_text_processor.py`, `tests/test_location_service.py` |
| API | `tests/test_api_properties.py`, `tests/test_api_contracts.py`, `tests/test_health.py` |
| Integrasjon | `tests/integration/test_api_crud.py`, `tests/integration/test_api_auth.py` |
| Eksterne API-er | `tests/test_frost_client.py`, `tests/test_nve_geo_client.py`, `tests/test_ssb_client_kpi.py` |
| KI Kollega | `tests/test_ki_kollega_comprehensive.py`, `tests/integration/test_ki_kollega_integration.py` |

---

## 3. Frontend – logikk og kode

### 3.1 Vitest (komponenttester)

```bash
cd frontend
npm run test
```

Kjører komponenttester (f.eks. `RiskPanel`, `DashboardStats`, `FinancialQueryPanel`).

### 3.2 Watch-modus (utvikling)

```bash
cd frontend
npm run test -- --watch
```

Reagerer på filendringer.

---

## 4. Brukerperspektiv – E2E og manuell test

### 4.1 Playwright E2E (produksjon)

Eksisterende smoke-tester kjører mot **produksjon** (`knowme-frontend-amber.vercel.app`):

```bash
cd frontend
npx playwright test
```

**Tester:**
- Dashboard laster med BEFS-tittel
- Stats viser data (ikke "...")
- Kart-komponent rendres
- Internkontroll-widget er synlig

**Merk:** Ved redirect til Microsoft-login vil noen tester hoppe over (auth kreves).

### 4.2 Playwright mot lokal utvikling

For å teste mot lokal frontend + backend:

1. **Oppdater `playwright.config.ts`** midlertidig:

```ts
use: {
    baseURL: 'http://localhost:3000',  // eller din lokale URL
    trace: 'on-first-retry',
},
```

2. **Start tjenestene:**

```bash
# Terminal 1 – backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2 – frontend
cd frontend && npm run dev
```

3. **Kjør Playwright:**

```bash
cd frontend && npx playwright test
```

### 4.3 Manuell brukertest – sjekkliste

Se [docs/TESTPLAN_RESPONSIV_UU.md](TESTPLAN_RESPONSIV_UU.md) for:
- Responsivitet (mobil, nettbrett, desktop)
- Tastaturnavigasjon
- Skjermleser-smoke
- Lighthouse/axe for tilgjengelighet

**Nøkkelsider å teste:**
- `/dashboard` – oversikt
- `/properties` – eiendomssøk
- `/properties/[id]` – eiendomsdetaljer
- `/contracts/[id]` – kontraktsdetaljer
- `/financials` – økonomi
- KI Kollega-chat (hvis tilgjengelig)

---

## 5. Full stack – anbefalt testflyt

### 5.1 Før commit (rask)

```bash
cd backend && make test
cd frontend && npm run test
```

### 5.2 Før deploy (mer omfattende)

```bash
# Backend – alle tester unntatt trege
cd backend && PYTHONWARNINGS=ignore pytest tests/ -m "not slow" -v

# Frontend – komponenttester
cd frontend && npm run test

# E2E mot produksjon (etter deploy)
cd frontend && npx playwright test
```

### 5.3 Etter deploy – verifiser produksjon

1. **Health-check:**
   ```bash
   curl https://striking-insight-production-a21b.up.railway.app/api/v1/health
   ```

2. **Autentisert API (med token):**
   ```bash
   curl -H "Authorization: Bearer <token>" \
        https://striking-insight-production-a21b.up.railway.app/api/v1/properties?limit=1
   ```

3. **Manuell innlogging** – sjekk at dashboard, eiendommer og kontrakter laster.

4. **Playwright smoke** – kjør `npx playwright test` mot produksjon.

---

## 6. Kodekvalitet og logikk

### 6.1 Linting

```bash
cd frontend && npm run lint
```

### 6.2 TypeScript

```bash
cd frontend && npx tsc --noEmit
```

### 6.3 Backend – import-sjekk

```bash
cd backend
python -c "from app.main import app; print('OK')"
```

---

## 7. CI/CD-anbefaling

For GitHub Actions eller tilsvarende:

1. **Backend:** `make test` (unit) + ev. `pytest tests/ -m "not slow and not integration"` uten DB
2. **Frontend:** `npm run test` + `npm run lint`
3. **E2E:** `npx playwright test` mot preview-URL etter deploy (Vercel preview)

Integrasjonstester som krever DB bør kjøres i et eget steg med `DATABASE_URL` satt.

---

## 8. Feilsøking

| Problem | Løsning |
|---------|---------|
| `tests/unit/` har få tester | Makefile kjører kun `tests/unit/`. Bruk `pytest tests/` for bredere dekning |
| Playwright feiler på login | Tester hopper over ved Microsoft redirect. Kjør mot lokal med mock-auth eller bruk testbruker |
| `DATABASE_URL` mangler | Integrasjonstester trenger DB. Sett fra `.env` eller bruk `-m "not requires_db"` |
| DSPy cache readonly | Golden set skippes. Sjekk at `tests/.pytest_dspy_cache` er skrivbar |
| Vitest finner ikke tester | Vitest ekskluderer `tests/**`. Komponenttester ligger i `*.test.tsx` ved siden av komponenter |

---

## 9. Kort referanse

| Mål | Kommando |
|-----|----------|
| Backend unit | `cd backend && make test` |
| Backend alle | `cd backend && pytest tests/ -v` |
| Backend coverage | `cd backend && make test-cov` |
| Frontend unit | `cd frontend && npm run test` |
| E2E produksjon | `cd frontend && npx playwright test` |
| Health-check | `curl https://striking-insight-production-a21b.up.railway.app/api/v1/health` |
