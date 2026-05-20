# Supabase-tilkobling fra Railway (backend)

Backend bruker **Session Pooler-URL** og **asyncpg** i database-connection-strengen. Her er hvorfor.

## 1. Hvorfor `pooler.supabase.com` (ikke `db.xxx.supabase.co`)?

Supabase sin direkte tilkobling (`db.xxx.supabase.co`) bruker kun **IPv6**. Railway sin gratis Hobby-plan støtter bare **IPv4**. Resultatet er:

- `[Errno 101] Network is unreachable` – serveren finner ikke nettverket.

**Løsning:** Bruk Supabase sin **Session Pooler** (`aws-1-...pooler.supabase.com`). Den snakker IPv4, som Railway Hobby forstår.

## 2. Hvorfor `postgresql+asyncpg://` (ikke bare `postgresql://`)?

Backend er asynkron og bruker **asyncpg**. Standard-strengen fra Supabase starter med `postgresql://`; da velger SQLAlchemy synkron driver (f.eks. psycopg2). Asynkron kode med synkron driver gir krasj.

**Løsning:** Legg til **+asyncpg** i URL-en: `postgresql+asyncpg://...` – da brukes riktig asynkron driver.

---

**Kort:** Pooler-URL gir IPv4 (Railway), `+asyncpg` gir riktig asynkron driver (Python).

---

**Se også:** Lokal utvikling med Docker bruker ofte hostnavnet `db` i `DATABASE_URL` (kun gyldig inne i compose-nettverket). Det er ikke det samme som produksjons-URL over internett — se [backend/README.md](../backend/README.md) (avsnitt om DATABASE_URL og Docker).
