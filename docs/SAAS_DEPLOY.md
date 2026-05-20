# SaaS-deploy (ny kunde, uten legacy-data)

Denne guiden beskriver hvordan du spinner opp en **egen instans** per kunde: ny kodebase-deploy, **tom database**, og ingen import av Bufetat-/BEFS-produksjonsdata.

## 1. Repository og miljø

- Klon prosjektet og opprett **egne** prosjekter for frontend (f.eks. Vercel) og backend (f.eks. Railway).
- Bruk **egne** hemmeligheter i hvert miljø; ikke gjenbruk `.env` fra Bufetat-produksjon.
- Sett `PRODUCT_PROFILE=saas` på backend og `NEXT_PUBLIC_MENU_PROFILE=saas` på frontend for å skjule offentlig-sektor-spesifikke menyer og å deaktivere en del integrasjons-APIer (se under).

## 2. Database

1. Opprett en **ny** PostgreSQL-instans (Railway, Supabase, Neon, e.l.).
2. Sett `DATABASE_URL` (asyncpg-URL: `postgresql+asyncpg://...`).
3. Kjør migrasjoner fra repo-roten:

```bash
cd backend && alembic upgrade head
```

4. **Ikke** restore dump fra eksisterende BEFS/Bufetat. Valgfri demo-eiendom: `SAAS_SEED_DEMO=1 .venv/bin/python scripts/saas_minimal_seed.py` (kun hvis `properties` er tom).

## 3. Backend-miljøvariabler (utdrag)

| Variabel | Anbefaling |
|----------|------------|
| `DATABASE_URL` | Påkrevd |
| `SECRET_KEY` | Sterk, unik nøkkel |
| `SUPABASE_JWT_SECRET` | Fra Supabase (anbefalt i produksjon) |
| `ALLOW_SHARED_SECRET_BYPASS` | `false` i produksjon når JWT er aktiv |
| `ADMIN_EMAILS` | Kommaseparert liste over administrator-e-poster |
| `PRODUCT_PROFILE` | `saas` for SaaS-profil, `full` for alt inkludert |
| `AI_ASSISTANT_NAME` | Vises i KI-prompts (standard: KI Kollega) |
| `AI_CUSTOMER_DOMAIN_LABEL` | Kort produktkontekst i KI-prompts (erstatt «BEFS eiendomsforvaltning») |
| `OPENAI_API_KEY` | For KI-Kollega |

Når `PRODUCT_PROFILE=saas` monteres ikke: Jira, BUP-lokasjoner, eksternt API-lag under `/api/external`, barnevern, SSB, krisesentre (`/api/v1/centers`).

## 4. Frontend-miljøvariabler (utdrag)

| Variabel | Anbefaling |
|----------|------------|
| `NEXT_PUBLIC_API_URL` | Backend-rot **uten** `/api/v1` |
| `NEXT_PUBLIC_MENU_PROFILE` | `saas` eller `full` (standard `full`) |
| `NEXT_PUBLIC_APP_SHORT_NAME` | Kort produktnavn i sidebar |
| `NEXT_PUBLIC_APP_TAGLINE` | Undertittel under logo |
| `NEXT_PUBLIC_APP_DEFAULT_TITLE` | Nettlesertittel (default) |
| `NEXT_PUBLIC_BOOTSTRAP_ADMIN_EMAILS` | Valgfri kommaseparert liste som **utvider** admin-sjekk i UI (i tillegg til rolle fra API). Uten hardkodede e-poster i koden må admin-rettigheter komme fra databasen eller denne variabelen. |

## 5. Drift per kunde (fase 1)

- Én deploy + én database per kunde gir **isolert data** uten `tenant_id` i skjemaet.
- Oppdater `FRONTEND_URLS` / CORS på backend for kundens domene.

## 6. Videre lesing

- [backend/.env.example](backend/.env.example) – flere variabler
- [frontend/lib/productMenu.ts](../frontend/lib/productMenu.ts) – hvilke menypunkter som skjules i `saas`-profil
