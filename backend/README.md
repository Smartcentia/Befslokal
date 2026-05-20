# BEFS Backend

## Oversikt
Dette er backend for "Bufetat Eiendomsforvaltningssystem" (BEFS), bygget med FastAPI og SQLAlchemy.

## Oppsett for utvikling

1. **Installer avhengigheter**:
    ```bash
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Miljøvariabler**:
    Kopier `.env.example` til `.env` og konfigurer:
    ```bash
    cp .env.example .env
    ```
    
    Viktige variabler:
    - `DATABASE_URL`: Tilkoblingsstreng for PostgreSQL.
    - `OPENAI_API_KEY`: API-nøkkel for OpenAI (kreves for KI Kollega).
    - `MAPBOX_ACCESS_TOKEN`: For kart og geokoding.
    - `RESEND_API_KEY`: For e-post og MFA.

### DATABASE_URL: lokal Docker vs produksjon

- **Docker Compose** med f.eks. `postgresql+asyncpg://...@db:5432/eiendom` er gyldig: `db` er et **internt servicenavn** i compose-nettverket, ikke et offentlig DNS-navn.
- **DNS-feil for `db`** når du kjører script eller klienter **fra vertsmaskinen** (utenfor containere) er **forventet** og betyr ikke nødvendigvis feil config for appen som kjører *inne* i Docker.
- **Script/CLI fra host**: Bruk tilkobling mot **localhost** (publisert Postgres-port) eller kjør med `docker compose exec <tjeneste> python …` slik at prosessen kjører **i samme nettverk** som databasen.
- **Produksjon (Railway/Supabase)**: Bruk full vert (Railway sin URL eller Supabase Session Pooler). Se [docs/SUPABASE_RAILWAY_TILKOBLING.md](../docs/SUPABASE_RAILWAY_TILKOBLING.md).

3. **Kjør serveren**:
    ```bash
    uvicorn app.main:app --reload
    ```

## Testing
Kjør tester med pytest:
```bash
pytest
```

## AI Kollega
For detaljer om AI-assistenten, se [README_KI_KOLLEGA.md](README_KI_KOLLEGA.md).
