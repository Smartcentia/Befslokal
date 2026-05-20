# Deployment Sjekkliste – Secrets & Auth

**Kilde:** CODE_REVIEW_30-01.md (Fix 1)  
**Formål:** Unngå 401 på autentiserte kall ved å sikre at SECRET_KEY og NEXTAUTH_SECRET er identiske.

---

## Vercel Deployment Protection (valgfritt ekstra lag)

Vercel **låser ikke** produksjons-URL automatisk. Uten beskyttelse kan hvem som helst laste frontend (HTML/JS). Appen kan i tillegg kreve innlogging på sikre ruter (f.eks. `/dashboard`).

**I Vercel:** Project → Settings → **Deployment Protection**

- **Standard Protection:** ofte aktivert for **Preview**-deployments (team/avhengig av plan).
- **Production:** må ofte aktiveres eksplisitt hvis du vil ha passord eller «Vercel Authentication» før siden vises.
- **Inkognitomodus** omgår ikke denne beskyttelsen; den gjelder før nettleseren får innhold.

Kombiner gjerne: **Deployment Protection** (skjul hele appen for omverdenen) **og** innlogging i appen (Supabase) for autoriserte brukere.

**Merk:** Ekte datasikkerhet krever også at API-et ikke stoler på hemmeligheter som er synlige i nettleseren (`NEXT_PUBLIC_*`). Se backend auth og `fetchAPI`-mønster.

---

## Brukere: ingen selvregistrering (kun administrator oppretter)

BEFS har ikke egen «registrer deg»-flyt i UI. Innlogging skjer med **Supabase Auth** (`signInWithPassword`). Nye brukere skal **ikke** kunne opprette konto selv.

### 1. Skru av offentlig sign-up i Supabase (obligatorisk)

I **Supabase Dashboard** → **Authentication** → **Providers** → **Email**:

- [ ] Slå **av** «Enable sign ups» / «Allow new users to sign up» (ordlyden kan variere med Supabase-versjon).
- Målet: Klienten (anon key) kan ikke registrere nye brukere; kun dere oppretter brukere fra Dashboard eller via Admin API senere.

Valgfritt: juster **Confirm email** etter behov for interne brukere.

### 2. Opprette brukere (drift)

**Supabase Auth** er kilden for innlogging (e-post + passord):

1. **Authentication** → **Users** → **Add user** (e-post og passord, eller invite etter deres valg).
2. **Backend/BEFS-database:** Første gang brukeren kaller API med gyldig JWT, kan `get_current_user` auto-opprette rad i `user`-tabellen hvis den mangler. Roller kan justeres av admin i BEFS, eller sett `ADMIN_EMAILS` i Railway for administrator-kontoer.

**Viktig:** `POST /api/v1/admin/users` i backend oppretter kun rad i Postgres – **ikke** bruker i Supabase Auth. For at noen skal kunne logge inn, må brukeren **først** finnes i Supabase (Alternativ A: manuelt i Dashboard). **Alternativ B (fremtidig):** utvide admin-endepunktet med Supabase Admin API (`auth.admin.createUser`) ved bruk av **service role**-nøkkel kun på server (`SUPABASE_SERVICE_ROLE_KEY` – aldri i frontend).

### 3. Frontend

- Rot (`/`) sender uinnloggede brukere til **/welcome**; innloggede ser oversikten.
- `/dashboard` krever sesjon (RequireAuth-layout).

---

### API: Supabase JWT mot backend (anbefalt i produksjon)

1. **Railway (backend):** Sett `SUPABASE_JWT_SECRET` til **JWT Secret** fra Supabase → Project Settings → API (samme verdi som brukes til å signere brukerens `access_token`).
2. Når `SUPABASE_JWT_SECRET` er satt, settes `ALLOW_SHARED_SECRET_BYPASS` automatisk til **false** (statisk delt hemmelighet i `Authorization` godtas ikke lenger som «admin»).
3. **Frontend (Vercel):** Ingen `NEXT_PUBLIC_*`-hemmelighet trengs for API-auth; nettleseren sender Supabase `session.access_token` etter innlogging.
4. **Nød / lokal dev:** `NEXT_PUBLIC_ALLOW_BACKEND_SECRET_BYPASS=true` i frontend og `ALLOW_SHARED_SECRET_BYPASS=true` på backend (kun midlertidig).

---

## 0. Railway-prosjekter

| Handling | Railway-prosjekt | Merknad |
|----------|------------------|---------|
| `railway up --detach` fra **repo-rot** | **lovely-bravery** | ✅ **PRODUKSJONS-backend** — `befs1-production.up.railway.app` |
| `railway run …` (CLI) | Avhenger av `railway link` | **Sjekk** med `railway status` før du kjører skript |

**`lovely-bravery` er produksjon.** `striking-insight` er et eldre/annet prosjekt. Bekreft alltid med `railway status` før du kjører alembic eller importskript.

---

## 1. Secret Synchronization

- [ ] Generer secret: `openssl rand -hex 32`
- [ ] Sett i **Railway:** Dashboard → BEFS1 → Environment → **SECRET_KEY**
- [ ] Sett i **Vercel:** Dashboard → knowme-frontend → Settings → Environment Variables → **NEXTAUTH_SECRET** (samme verdi)
- [ ] Verifiser: første 8 tegn skal være identiske begge steder

---

## 2. Environment Variables

**Railway (Backend):**
- `SECRET_KEY` = 64-tegn hex (samme som NEXTAUTH_SECRET)
- `OPENAI_API_KEY`, `DATABASE_URL`, `BACKEND_CORS_ORIGINS`, `ADMIN_EMAILS`, `ENVIRONMENT=production`

**Vercel (Frontend):**
- `NEXTAUTH_SECRET` = samme 64-tegn hex som Railway sin SECRET_KEY
- `NEXTAUTH_URL`, `NEXT_PUBLIC_API_URL` = `https://knowme-backend-production.up.railway.app` (backend base-URL uten /api/v1)
- `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` = Mapbox public token (pk.eyJ1...) – **påkrevd for kart**. Hent fra [Mapbox Account](https://account.mapbox.com/access-tokens/)

---

## 3. Test Authentication

- [ ] Deploy backend (Railway)
- [ ] Deploy frontend (Vercel)
- [ ] Test login i nettleser
- [ ] Test autentisert API-kall (f.eks. /api/v1/properties)
- [ ] Verifiser 200 OK (ikke 401)

---

## Ved 401-feil

1. Sjekk at SECRET_KEY (Railway) og NEXTAUTH_SECRET (Vercel) er **identiske** (kopier- lim inn på nytt).
2. Redeploy begge tjenester etter endring av secrets.
3. Se også: FIX_SECRET_MISMATCH.md, SEKRETS_SYNKRONISERT_NESTE_STEG.md

---

## Siste deploy (referanse)

| Plattform | Deploy ID / Commit |
|-----------|--------------------|
| **Vercel** | `d0f5592d6bdcfb03601c6bbea7686dfa` |

---

## Verifisert fungerende

**30. januar 2026:** Eiendommer, kontrakter og øvrige autentiserte kall virker etter at **feil verdier i Vercel og Railway** ble rettet (SECRET_KEY = NEXTAUTH_SECRET). Ved neste deploy: sjekk at begge fortsatt er identiske.
