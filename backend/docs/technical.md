# Teknisk dokumentasjon – BEFS

## Systemoversikt

BEFS (Bufetat Eiendomsforvaltningssystem) består av:
* **Frontend:** Next.js på Vercel
* **Backend:** FastAPI på Railway
* **Database:** PostgreSQL (Supabase)

---

## Deploy

### Frontend (Vercel)
* **Auto-deploy:** `git push origin main` – Vercel deployer automatisk
* **URL:** https://knowme-frontend-amber.vercel.app
* **Viktig:** `NEXT_PUBLIC_API_URL` må peke på backend (base-URL uten /api/v1)

### Backend (Railway)
* **Auto-deploy:** Ved push til main hvis repo er koblet
* **Manuelt:** Railway Dashboard → tjenesten → Deploy
* **URL:** https://knowme-backend-production.up.railway.app
* **Health:** https://knowme-backend-production.up.railway.app/api/v1/health

### Secrets
* **SECRET_KEY** (Railway) og **NEXTAUTH_SECRET** (Vercel) må være **identiske**
* Generer: `openssl rand -hex 32`
* **NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN** (Vercel): Mapbox public token for kart. Sett i Vercel → Settings → Environment Variables. **Redeploy** etter endring (NEXT_PUBLIC_* bakes inn ved build).

---

## Risikovurdering – metodikk

Risikoscoren (0–100) bygger på en forenklet modellidé: **R ≈ P × C** (risiko ≈ sannsynlighet × konsekvens).

**Viktig presisering:** P og C representerer her **proxy-indikatorer**, ikke faktiske sannsynligheter eller kroner. Scoren er en relativ prioriteringsindikator, ikke «ekte» risiko i form av forventet tap (E[skade]). Bruk den til å rangere eiendommer etter oppfølgingsbehov, ikke som absolutt risikomål.

**Full metodikk:** Se `docs/RISK_OG_KOSTNADSANALYSE_METODIKK.md` for prioriteringsindeks, reservefaktor og styringsklasser.

### Prioriterings-API

| Endepunkt | Beskrivelse |
|-----------|--------------|
| `GET /api/v1/risk/prioritized?year=2026` | Eiendommer sortert etter prioriteringsindeks. Returnerer `property_id`, `risk_score`, `annual_cost`, `priority_index`, `reserve_factor`, `budget_by_category`, `open_deviations`. Brukes av Risikobildet. |

---

## Kostnadsanalyse (cost-analysis)

Backend-endepunkt: `GET /api/v1/properties/{id}/cost-analysis`  
Implementasjon: `backend/app/services/analytics/cost_analysis_service.py`

### Datakilder
* **Kostnader:** `external_data.financials.manual_expenses` (liste med `type`, `provider`, `amount`, `date`)
* **Husleie:** Sum av årlig leie fra aktive kontrakter, eller fallback til `external_data.financials.rent_summary`
* API returnerer `synthetic_rent: true` når husleie er estimat

### Beregningslogikk
1. Hent alle utgifter fra `manual_expenses` (ingen årfiltrering – se caveat nedenfor)
2. Kategoriser hver utgift via `EXPENSE_CATEGORY_MAP` (type → CostCategory)
3. Summer per kategori: property, operations, investment, other
4. Beregn forhold: `ratio = kategori_sum / annual_rent` (f.eks. total_ratio = total_costs / annual_rent)
5. Sammenlign med `EXPECTED_RATIOS` for vurdering
6. Detekter anomalier (poster > 500k) og duplikater (provider+amount gruppert)

### Håndtering av manglende husleie (annual_rent = 0)
Ved `annual_rent = 0` eller manglende husleiedata settes alle ratioer til 0 for å unngå deling på null og meningsløse verdier. Vurderingsgrenser (KRITISK/HØY/MODERAT) gis da ikke. Løsning: Legg til kontrakter eller `rent_summary` i `external_data.financials`.

### Caveat: total_costs vs. annual_rent (årlighet)
`total_costs` er summen av **alle** poster i `manual_expenses` uten årfiltrering. `annual_rent` er årlig leie. Tersklene (f.eks. total_ratio > 3.0) gir kun mening når begge er **per år**. Hvis `manual_expenses` inneholder utgifter fra flere år, blir `total_costs` flerårig og ratioene systematisk for høye uten at det nødvendigvis er «kritisk». Vurder å filtrere utgifter på år (f.eks. siste 12 mnd) før ratio-beregning.

### Kostnadskategorier (EXPENSE_CATEGORY_MAP)
| Kategori | Eksempler på typer |
|----------|--------------------|
| property | Leie lokaler, Fellesutgifter, Leie parkeringsplass |
| operations | Strøm og oppvarming, Renhold lokaler, Vakthold, Annen kostnad lokaler, Reparasjon/vedlikehold |
| investment | Fast bygningsinventar > 50k, Oppgradering, Ombygging, Risikoavsetning |
| other | Alt som ikke matcher |

### Forventede forhold (EXPECTED_RATIOS)
| Kategori | Min | Maks | Typisk |
|----------|-----|------|--------|
| property | 80% | 200% | 120% |
| operations | 5% | 50% | 15% |
| investment | 0% | 100% | 10% |

### Vurderingsgrenser (total_ratio vs. husleie)
* `> 3.0` → KRITISK
* `> 2.0` → HØY
* `> 1.5` → MODERAT
* ellers → NORMAL

### Mangler enheter
Eiendommer uten registrerte **enheter** (leiligheter/lokaler) får varsel "Mangler enheter". Leie-estimatet kan da være unøyaktig. Løsning: Legg til enheter.

---

## Database

* **Host:** Supabase PostgreSQL
* **Driver:** asyncpg (async SQLAlchemy)
* **Migrasjoner:** `cd backend && alembic upgrade head`
* **Ny migrasjon:** `alembic revision --autogenerate -m "beskrivelse"`

### Nøkkeltabeller
| Tabell | Beskrivelse |
|--------|-------------|
| properties | Eiendommer |
| units | Enheter (leiligheter, lokaler) |
| contracts | Kontrakter |
| parties | Parter (leietakere, eiere) |
| deviations | Avvik (FDV) |
| risk_assessments | Risikovurderinger |
| internal_control_cases | Internkontroll-saker |
| checklist_templates | Sjekklistemaler (system + brukerdefinerte) |

---

## Internkontroll og sjekklister

### API-endepunkter

| Endepunkt | Beskrivelse |
|-----------|-------------|
| `GET /api/v1/internal-control/cases` | Hent internkontroll-saker (filtrert på property_id, status) |
| `GET /api/v1/internal-control/cases/{id}` | Hent én sak |
| `PATCH /api/v1/internal-control/cases/{id}` | Oppdater sak (status, notes) |
| `POST /api/v1/internal-control/cases/{id}/complete-checklist` | Fullfør sjekkliste (responses, notes) |
| `POST /api/v1/internal-control/cases/create-initial-for-property/{property_id}` | Opprett standard saker for eiendom |
| `POST /api/v1/internal-control/cases/from-template` | Opprett sak fra ChecklistTemplate (body: template_id, property_id) |
| `POST /api/v1/internal-control/process-overdue` | Prosesser forfalte saker (ADMIN, cron) |
| `GET /api/v1/checklists/templates?scope=my\|shared\|all` | Hent sjekklistemaler |
| `POST /api/v1/checklists/templates` | Opprett brukerdefinert mal |
| `PUT /api/v1/checklists/templates/{id}` | Oppdater mal (kun eier) |
| `DELETE /api/v1/checklists/templates/{id}` | Slett mal (kun eier) |

### Brukerdefinerte sjekklister
* Maler har `scope`: system, user, region, global. Bruker-maler har `created_by_user_id`.
* `scope=my` viser kun egne maler, `shared` system/delte, `all` alle.

---

## Parter – API og tjenester

| Endepunkt | Beskrivelse |
|-----------|-------------|
| `POST /api/v1/parties/{id}/company-summary` | Hent AI-oppsummering av bedrift fra nettet (OpenAI). Lagres i `external_data.openai_company_summary`. |
| `POST /api/v1/parties/{id}/enrich-brreg` | Hent/oppdater BRREG-data (Brønnøysundregistrene). |
| `POST /api/v1/parties/{id}/due-diligence` | Kjør risikovurdering (Due Diligence). Søker nettet (konkurs, rettssak, svindel, erfaringer, regnskapstall), sender til LLM, returnerer `risk_level`, `red_flags`, `sources`. Lagres i `external_data.due_diligence_report`. |

**Due Diligence:** Krever `OPENAI_API_KEY` og MCP web-søk. Se `app/services/due_diligence_service.py`.

---

## Bufdir-pipeline

| Steg | Script | Beskrivelse |
|------|--------|-------------|
| 1 | fetch_bufdir_data.py | Henter liste-data fra bufdir.no |
| 2 | match_bufdir_robust.py | Matcher mot eiendommer i DB |
| 3 | enrich_properties_bufdir.py | Laster ned bilder, fyller external_data |
| 4 | establish_bufdir_unmatched.py | Oppretter nye eiendommer for umatchade |
| 5 | fetch_images_for_barnevern.py | Søker bilder for barnevern (valgfritt). Kjør: `./scripts/kjor_fetch_barnevern_images.sh` |

---

## Brukerhjelp

* **Kilde:** `docs/BRUKERHJELP.md` – parses av help_service
* **API:** `GET /api/v1/help/` (liste), `GET /api/v1/help/{id}` (innhold)
* **Teknisk doc:** `docs/technical.md` (denne filen)

---

## Feilsøking

### Backend health feiler
* Sjekk DATABASE_URL i Railway
* Sjekk logs: Railway Dashboard → Logs

### 401 på autentiserte kall
* Verifiser at SECRET_KEY (Railway) = NEXTAUTH_SECRET (Vercel)
* Redeploy begge tjenester etter endring

### Kostnadsanalyse viser "Mangler husleiedata"
* Sjekk at eiendommen har `external_data.financials.rent_summary` for syntetisk fallback
* Eller legg til enheter og kontrakter

### Due Diligence / risikovurdering feiler
* Sjekk at `OPENAI_API_KEY` er satt i Railway
* MCP web-søk må være tilgjengelig (search_web_tool)
* Se Railway-logg for detaljert feilmelding

### Kart viser «Sett NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN»
* **Vercel:** Sett `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` i Vercel Dashboard → Project → Settings → Environment Variables (Production + Preview)
* **Redeploy:** Etter å ha lagt til variabelen, gjør en ny deploy (Deployments → ⋮ → Redeploy). NEXT_PUBLIC_* bakes inn ved build.
* **Token:** Må starte med `pk.` (public token). Hent fra [Mapbox Access Tokens](https://account.mapbox.com/access-tokens/)
* **URL-restriksjoner:** Hvis token har URL-restriksjoner, sørg for at Vercel-domene (f.eks. knowme-frontend-amber.vercel.app) er tillatt
