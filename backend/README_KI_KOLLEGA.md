# KI Kollega - Komplett Oversikt

## Hva er KI Kollega?

KI Kollega er en multi-agent AI-assistent for BEFS Eiendom som hjelper brukere med spørsmål om eiendommer, kontrakter, dokumenter og analyser. Systemet bruker LangGraph for agent-orchestrering og støtter både dokument-søk (RAG) og SQL-generering.

---

## 🚀 Rask Start

### Test KI Kollega lokalt:

```bash
# Start backend
cd backend
python3 run_server.py

# Test via API
curl -X POST http://localhost:8000/api/v1/ki-kollega/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Gi meg den største eiendommen"}'
```

### Deploy til produksjon:

```bash
# Backend (Railway)
# Deploy: git push (auto) eller Railway Dashboard → Deploy

# Frontend (Vercel)
# Automatisk deploy ved git push til main
```

---

## 📚 Dokumentasjon

### Hoveddokumenter:

1. **[KI_KOLLEGA_ARKITEKTUR.md](./KI_KOLLEGA_ARKITEKTUR.md)**
   - Komplett arkitektur-dokumentasjon
   - Multi-agent workflow
   - Feilhåndtering og timeout-strategier
   - Deployment og infrastruktur

2. **[IMPLEMENTERTE_FORBEDRINGER.md](./IMPLEMENTERTE_FORBEDRINGER.md)**
   - Alle implementerte forbedringer
   - Hybrid LLM-routing
   - SQL caching
   - Retry-logikk
   - Hybrid SQL-strategi

3. **[HYBRID_SQL_STRATEGI.md](./HYBRID_SQL_STRATEGI.md)**
   - Hybrid SQL-strategi med fallback til gpt-4o
   - Kompleksitets-deteksjon
   - Kostnad-analyse
   - Best practices

4. **[OPENAI_4O_MINI_BRUK.md](./OPENAI_4O_MINI_BRUK.md)**
   - Hvordan gpt-4o-mini brukes i systemet
   - Kostnad-analyse
   - Konfigurasjon
   - Best practices

5. **[DAGENS_ENDRINGER_2026_01_27.md](./DAGENS_ENDRINGER_2026_01_27.md)**
   - Oppsummering av alle endringer gjort i dag
   - Test-resultater
   - Ytelsesforbedringer

### Testing:

- **[tests/README.md](./tests/README.md)** - Testing-guide (golden set, DSPy cache, skip i readonly-miljø)
- **[tests/TEST_RESULTATER.md](./tests/TEST_RESULTATER.md)** - Test-resultater

**KI Kollega test-filer:**

| Fil | Dekker | Avhengigheter |
|-----|--------|----------------|
| `tests/test_ki_kollega_comprehensive.py` | Init, chat uten db, timeout, kilder (liste/streng), verktøy, SQL-sikkerhet, proactive insights, API (health, suggestions, proactive, chat) | Ingen DSPy/LLM |
| `tests/test_ki_kollega_golden_set.py` | Supervisor-routing, SQL-mønstre, JSONB, ev. SQL-kjøring | DSPy (skrivbar cache), ev. DB/OpenAI |
| `tests/integration/test_ki_kollega_integration.py` | Init, chat timeout, chat success med mock | Mock av graf |

**Kjøre tester:**
```bash
cd backend
# Comprehensive + integrasjon (anbefalt i CI)
pytest tests/test_ki_kollega_comprehensive.py tests/integration/test_ki_kollega_integration.py -v
# Golden set (krever DSPy cache skrivbar)
pytest tests/test_ki_kollega_golden_set.py -v
```

**DSPy cache:** `conftest.py` setter `DSPY_CACHEDIR` til `tests/.pytest_dspy_cache`. I readonly-miljø skippes golden set-modulen; comprehensive og integrasjon kjører uansett.

### Database:

- **[app/config/SCHEMA.md](./app/config/SCHEMA.md)** - Database schema med JSONB-eksempler

---

## 🏗️ Arkitektur

### Multi-Agent Workflow

```
User Query
    ↓
KIKollegaService.chat()
    ├── Henter memories (AgentMemoryService)
    ├── Henter persona
    ├── Discover tools (ToolDiscoveryService)
    └── Starter LangGraph
        ↓
    SUPERVISOR → GUARDIAN → RESEARCHER → ANALYST → WRITER
```

### Agent-roller

| Agent | Ansvar | Teknologi |
|-------|--------|-----------|
| **Supervisor** | Routing basert på spørsmål | Keyword + LLM (gpt-4o-mini) |
| **Guardian** | Sikkerhetssjekk | Keyword-filtering |
| **Researcher** | Søker i dokumenter/DB/web | RAG (hybrid search) |
| **Analyst** | SQL-generering/kjøring | DSPy (gpt-4o-mini/gpt-4o) |
| **Action** | Utfører operasjoner (HitL) | Verktøy-kall med UI-godkjenning |
| **Writer** | Syntetiserer svar | OpenAI (gpt-4o-mini) |

---

## ✨ Nye Funksjoner (Februar 2026)

### 1. Human-in-the-Loop (Action Node)
- Tillater KI Kollega å foreslå systemhandlinger (f.eks. Jira-saker)
- Pauser utførelsen via `pending_action` for sikret brukergodkjenning
- Gjenopptar flyten etter at brukeren verifiserer handlingen i chat-grensesnittet


## ✨ Nye Funksjoner (Januar 2026)

### 1. Hybrid LLM-Routing
- Kombinerer keyword-matching med LLM-klassifisering
- Håndterer tvetydige spørsmål bedre
- Fallback til keyword-routing ved feil

### 2. SQL Caching
- Cache for spørsmål → SQL mapping
- ~75% reduksjon i LLM-kall
- TTL-basert utløp (1 time)

### 3. Retry-logikk
- Eksponensiell backoff ved database-feil
- Håndterer database cold starts
- Maks 3 retry-forsøk

### 4. Hybrid SQL-strategi
- Automatisk valg mellom gpt-4o-mini og gpt-4o
- Kompleksitets-deteksjon (JSONB, JOINs, aggregering)
- Proaktiv og reaktiv fallback

### 5. Golden Set Testing
- Komplett test-suite med 8+ test cases
- Automatisk validering av kritiske funksjoner

---

## 📊 Ytelsesforbedringer

| Metrikk | Før | Etter | Forbedring |
|---------|-----|-------|------------|
| SQL-generering LLM-kall | 100% | ~25% | 75% reduksjon |
| Routing-akkurathet | Keyword-only | Hybrid | Bedre |
| Database-feilrate | Ingen retry | Retry ved transient errors | Redusert |
| Kostnad per samtale | ~$0.0036 | ~$0.0003 | 92% reduksjon |

---

## 🧪 Testing

### Kjør tester:

```bash
# Routing test
PYTHONPATH=/Users/frank/Documents/BEFS_CLEAN/backend python3 tests/test_supervisor_routing.py

# Kompleksitets-deteksjon test
PYTHONPATH=/Users/frank/Documents/BEFS_CLEAN/backend python3 tests/test_complexity_detection.py

# Alle tester (krever database + DSPy)
cd backend
pytest tests/ -v
```

### Test-resultater:

- ✅ Supervisor Routing: 6/6 tester bestått
- ✅ Kompleksitets-deteksjon: 10/10 tester bestått
- ✅ Keyword-deteksjon: 14/14 tester bestått

**Totalt**: 30/30 tester bestått (100% suksessrate)

---

## 🔧 Konfigurasjon

### Miljøvariabler:

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # Standard modell

# Database
DATABASE_URL=postgresql+asyncpg://...

# Auth
SECRET_KEY=...  # Må matche NEXTAUTH_SECRET i frontend
```

### Konfigurerbare funksjoner:

```python
# Hybrid routing
USE_HYBRID_ROUTING = True  # Aktiver/deaktiver LLM-routing

# SQL caching
SQL_CACHE_ENABLED = True
SQL_CACHE_TTL_SECONDS = 3600  # Cache TTL (1 time)
SQL_CACHE_MAX_SIZE = 100  # Maks cache size
```

---

## 📈 Monitoring

### Cache-statistikk:

```python
from app.services.dspy.sql_generator import dspy_generator

stats = dspy_generator.get_cache_stats()
# {
#   "cache_enabled": True,
#   "cache_size": 42,
#   "cache_hits": 150,
#   "cache_misses": 50,
#   "hit_rate_percent": 75.0,
#   "fallback_used": 12,  # Antall ganger gpt-4o ble brukt
#   "cached_mini": 30,
#   "cached_fallback": 12
# }
```

### Viktige metrics å spore:

- Cache hit rate
- Fallback usage (hvor ofte gpt-4o brukes)
- Routing-akkurathet
- Database retry-rate
- LLM token-bruk og kostnad

---

## 🐛 Feilsøking

### Vanlige problemer:

1. **Database-feil**: Sjekk `DATABASE_URL` og Supabase-status
2. **LLM-feil**: Sjekk `OPENAI_API_KEY` og rate limits
3. **Routing-feil**: Sjekk logger for routing-beslutninger
4. **SQL-feil**: Sjekk cache-statistikk og fallback usage

### Debugging:

```python
# Se cache-statistikk
stats = dspy_generator.get_cache_stats()

# Tøm cache
dspy_generator.clear_cache()

# Test kompleksitets-deteksjon
is_complex = dspy_generator._detect_complexity("spørsmål")
```

---

## 📝 Changelog

### 27. Januar 2026
- ✅ Implementert hybrid LLM-routing
- ✅ Implementert SQL caching
- ✅ Implementert retry-logikk
- ✅ Implementert hybrid SQL-strategi
- ✅ Fikset 6 kritiske feil
- ✅ Opprettet Golden Set testing
- ✅ Oppdatert all dokumentasjon

**Se**: `DAGENS_ENDRINGER_2026_01_27.md` for detaljer

---

## 🤝 Bidrag

### Legge til nye funksjoner:

1. Implementer funksjonaliteten
2. Legg til tester i `tests/`
3. Oppdater dokumentasjonen
4. Kjør tester og verifiser

### Rapportere bugs:

1. Sjekk eksisterende issues
2. Opprett ny issue med detaljer
3. Inkluder logger-output og test-cases

---

## 📞 Support

- **Dokumentasjon**: Se dokumentasjonsfiler over
- **Testing**: Se `tests/README.md`
- **Deployment**: Se `HVOR_DEPLOYE.md` og `GIT_COMMIT_DEPLOY.md`

---

**Sist oppdatert**: Februar 2026
**Status**: ✅ Produksjonsklar
**Versjon**: 2.1 (med Human-in-the-Loop Actions)
