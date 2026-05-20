# Befslokal

**100 % lokal** utgave av BEFS (Bufetat Eiendomsforvaltningssystem), migrert fra [BEFS1](https://github.com/Smartcentia/BEFS1).

Ingen avhengighet av Vercel, Railway, Supabase sky eller OpenAI API. Alt kjører på din maskin via Docker:

| Tjeneste | Erstatter | Port |
|----------|-----------|------|
| PostgreSQL + pgvector | Supabase/Railway DB | 5432 |
| FastAPI backend | Railway | 8000 |
| Next.js frontend | Vercel | 3000 |
| Ollama + **Mistral** (7B) | OpenAI GPT | 11434 |
| Lokal bruker-DB + passord | Supabase Auth | — |

## Krav

- Docker Desktop (eller Docker Engine + Compose v2)
- Minst **8 GB RAM** (Mistral 7B)
- Ca. **5 GB disk** for modeller (første gang)

## Kom i gang (én kommando)

```bash
chmod +x scripts/befslokal-up.sh scripts/befslokal-init-db.sh
./scripts/befslokal-up.sh
```

Første oppstart laster ned Mistral og `nomic-embed-text` (RAG) – kan ta 5–15 minutter.

### Innlogging

| E-post | Passord | Rolle |
|--------|---------|-------|
| `admin@befslokal.no` | `befslokal123` | ADMIN (standard) |
| `admin@bufdir.no` | `test123` | ADMIN (hvis test-seed kjører) |

Åpne **http://localhost:3000** → Logg inn.

## Manuell database-init

Hvis migrasjoner ikke kjørte ved oppstart:

```bash
./scripts/befslokal-init-db.sh
```

## Utvikling uten Docker (valgfritt)

**Backend:**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.befslokal .env
# Start Ollama lokalt: ollama pull mistral
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Sett `LOCAL_AI_STATION_URL=http://localhost:11434/v1` i backend når Ollama kjører på vertsmaskinen.

## KI (Mistral via Ollama)

- Chat/KI-Kollega: modell **`mistral`** (letteste Mistral)
- Embeddings/RAG: **`nomic-embed-text`**
- Konfigurasjon: `USE_LOCAL_AI=true` i `backend/.env.befslokal`

## Migrere data fra produksjon

1. Eksporter PostgreSQL fra Supabase/Railway (`pg_dump`).
2. Importer til lokal DB:

```bash
docker compose exec -T db psql -U postgres -d eiendom < dump.sql
```

3. Kjør `./scripts/befslokal-init-db.sh` for admin-bruker om nødvendig.

## GitHub-repo

Dette prosjektet skal ligge i **Smartcentia/Befslokal** (nytt repo, ikke BEFS1):

```bash
git remote set-url origin https://github.com/Smartcentia/Befslokal.git
git push -u origin main
```

(Opprett repo på GitHub først om det ikke finnes.)

## Opprinnelse

Full kodebase migrert fra BEFS1. Sky-spesifikke deploy-scripts (`vercel-auto-redeploy.sh`, `railway.toml`) er beholdt som referanse men brukes ikke i Befslokal.

## Feilsøking

| Problem | Løsning |
|---------|---------|
| KI svarer ikke | `docker compose logs ollama` – vent til `ollama pull mistral` er ferdig |
| 401 på API | Sjekk at du er innlogget; `SECRET_KEY` = `befs-super-secret-key-12345` |
| Tom database | `./scripts/befslokal-init-db.sh` |
| Frontend blank API | `NEXT_PUBLIC_API_URL` må være `http://localhost:8000` ved build |
