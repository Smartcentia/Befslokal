# Railway: «Error creating build plan with Railpack» og «context canceled»

## Årsak

Tjenesten **striking-insight** (backend) bygges fra **repo-roten**. I et monorepo (frontend + backend) prøver Railpack å oppdage prosjekttype i roten og får ikke til en entydig build-plan, derfor feilen.

## Løsning

Sett **Root Directory** for backend-tjenesten til **`backend`** slik at Railway kun bygger fra backend-mappen. Da brukes `backend/Dockerfile` og bygget skal gå gjennom.

### Steg i Railway Dashboard

1. Gå til [Railway](https://railway.app) og åpne prosjektet (f.eks. «striking-insight»).
2. Velg tjenesten **striking-insight** (backend).
3. Gå til **Settings**.
4. Finn **Root Directory** (under Build).
5. Sett verdien til: **`backend`** (uten avsluttende `/`).
6. Lagre og trigger en ny deploy (Redeploy eller push til main).

Etter dette bygger Railway kun fra `backend/`, finner `Dockerfile` der og bruker den (jf. `backend/railway.toml` som setter `builder = "DOCKERFILE"`).

### Config as code

I `backend/railway.toml` er det satt:

- `builder = "DOCKERFILE"` – bruk Dockerfile, ikke Railpack.
- `healthcheckPath = "/api/v1/health"` – valgfri healthcheck.

Config-filen brukes når Root Directory er satt til `backend`; da leses `backend/railway.toml` automatisk.

### Hvis du bruker Railway CLI

Når du er koblet til riktig tjeneste, kan du trigge ny deploy etter at Root Directory er satt i Dashboard:

```bash
railway up
```

Eller redeploy fra Dashboard etter endring av Root Directory.

---

## Hvis «WORKDIR /app mount callback failed … context canceled»

- **Årsak:** Bygg-context for stor eller timeout på Railway under mount.
- **Gjort:** `backend/.dockerignore` er utvidet (logs, e-don*.txt, tests, .pytest_cache m.m.) for å redusere context.
- **Anbefaling:** I Railway → striking-insight → **Settings** → **Build**: slå på **«Use Metal Build Environment»** og redeploy.
