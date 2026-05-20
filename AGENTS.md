# BEFS / KNOWME – Codex Instructions

Bufetat Eiendomsforvaltningssystem: property management for Bufetat with contracts, financials, HMS deviations, and KI-Kollega (AI assistant).

## Stack

- **Frontend**: Next.js 16, React 19, TypeScript 5, TailwindCSS 4 → Vercel
- **Backend**: Python 3.11, FastAPI 0.115, SQLAlchemy 2 (async), Alembic → Railway
- **Database**: PostgreSQL + pgvector (Railway internal URL)
- **Auth**: Supabase (frontend session) + shared secret Bearer token (backend bypass)
- **AI**: OpenAI GPT-4o via LangGraph/LangChain

## Local development

**Frontend** (port 3000):
```bash
cd frontend && npm install && npm run dev
```

**Backend** (port 8000):
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Migrations**:
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Deploy

**Backend** – always from `backend/` subdirectory:
```bash
cd backend && railway up --detach
```

**Frontend** – **run from repo root** (Vercel project has Root Directory = `frontend`; running from `frontend/` breaks path resolution):
```bash
cd /path/to/BEFS_CLEAN && vercel --prod
```
Alias is set automatically to `knowme-frontend-amber.vercel.app`. If needed: `vercel alias [deployment-url] knowme-frontend-amber.vercel.app`.

> `NEXT_PUBLIC_API_URL` is baked at build time. Change it in Vercel env **before** deploying.

## Key environment variables

| Variable | Where | Notes |
|---|---|---|
| `DATABASE_URL` | Backend | `postgresql+asyncpg://...` Railway internal |
| `OPENAI_API_KEY` | Backend | Required for KI-Kollega |
| `NEXT_PUBLIC_API_URL` | Frontend | Railway backend URL, baked at build |
| `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` | Frontend | Required for maps |
| `RESEND_API_KEY` | Backend | Email / MFA |
| `SECRET_KEY` | Backend | JWT signing |

## Architecture rules (critical)

1. **Never use named PostgreSQL enum types** – use `Column(String)` or `native_enum=False`. Named PG enums crash Railway on every query.
2. **Always catch `Exception`** (not `ImportError`) in services that query optional tables (e.g. `budget`, `gl_transaction`).
3. **ADMIN role short-circuits** access checks – never run N×DB loops for contract/property filtering. Use `get_user_accessible_property_ids()` once.
4. **Do not add `logger.info` on per-request property access** – causes Railway log rate-limit (500 logs/sec). Use `logger.debug`.
5. **PostGIS / geom removed** from Property model – do not re-add without migration.
6. **Tailwind v4** – custom colors used in utilities (e.g. `text-primary-foreground`, `text-muted-foreground`) must be declared in `frontend/app/globals.css` inside `@theme { }` as `--color-<name>: var(--<css-var>);`. Missing entries cause Vercel build failure ("Cannot apply unknown utility class").

## Auth flow

```
Browser → fetchAPI() → Bearer <shared-secret> + X-User-Email header
→ auth_middleware.py → shared-secret bypass = system@befs.no ADMIN
→ normal path = X-User-Email DB lookup → role injected into request state
```

Role RBAC:
- `ADMIN` → all properties/contracts
- `REGIONAL_MANAGER` → properties in `user.region`
- `PROPERTY_MANAGER` / `JANITOR` → assigned properties via `user_property_association`
- `TENANT` → read-only

## File conventions

- Do **not** remove existing functions unless explicitly asked
- Do **not** rewrite entire files for single-method changes
- Check existing imports before adding new ones
- Edit only the specific lines that need changing

## Testing

```bash
cd backend && make test       # unit-tester (uten advarsler)
cd backend && make test-cov   # med coverage
cd backend && pytest         # alle tester
cd frontend && npm run test   # Vitest
```

## Production URLs

- Frontend: `https://knowme-frontend-amber.vercel.app`
- Backend: `https://striking-insight-production-a21b.up.railway.app`
- Health: `GET /api/v1/health`

## Verktøy og tilkoblinger

- **Supabase**: Database (PostgreSQL) og auth. CLI (`supabase`) og MCP tilgjengelig (`.cursor/mcp.json`).
- **Vercel**: Frontend-deploy. CLI (`vercel`) og MCP tilgjengelig.
- **Railway**: Backend-deploy og (ved behov) database. CLI (`railway`) og MCP tilgjengelig.

`DATABASE_URL` for backend kommer typisk fra Railway (intern Postgres) eller Supabase Session Pooler (se [docs/SUPABASE_RAILWAY_TILKOBLING.md](docs/SUPABASE_RAILWAY_TILKOBLING.md)). Script som trenger DB (f.eks. `backend/scripts/export_eiendommer_json.py`) må kjøres med `DATABASE_URL` satt (f.eks. fra `backend/.env` eller `railway run`).
