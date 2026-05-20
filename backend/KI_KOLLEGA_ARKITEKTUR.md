# KI Kollega - Arkitektur og Feilhåndtering

## Oversikt

KI Kollega er en multi-agent AI-assistent bygget med LangGraph som håndterer spørsmål om eiendommer, kontrakter og dokumenter. Dette dokumentet dekker arkitektur, feilhåndtering, timeout-strategier og testing.

---

## Arkitektur

### Multi-Agent Workflow

```
User Query
    ↓
KIKollegaService.chat()
    ├── Henter memories (AgentMemoryService)
    ├── Henter persona
    ├── Discover tools (ToolDiscoveryService)
    ├── Sidekontekst: ved entity_type/entity_id hentes sammendrag (kontrakt/part/eiendom) og injiseres som «BRUKEREN SER PÅ» i meldingslisten
    └── Starter LangGraph
        ↓
    SUPERVISOR → GUARDIAN → RESEARCHER → ANALYST → WRITER
```

### Agent-roller

| Agent | Ansvar | Feil-scenarioer |
|-------|--------|-----------------|
| **Supervisor** | Routing basert på spørsmål | Uklart spørsmål → Default til Researcher |
| **Guardian** | Sikkerhetssjekk | Blokkerer sensitive forespørsler → Writer med forklaring |
| **Researcher** | Søker i dokumenter/DB/web | Ingen resultater → Router til Analyst |
| **Analyst** | SQL-generering/kjøring | SQL-feil → Returnerer error til Writer |
| **Writer** | Syntetiserer svar | LLM-feil → Fallback til enkel tekst |

---

## Feilhåndtering

### 1. Timeout-håndtering

**Chat Timeout (45 sekunder)**:
```python
CHAT_TIMEOUT_SECONDS = 45.0
```

**Hva skjer ved timeout:**
- LangGraph workflow avbrytes
- Bruker får vennlig melding: "Forespørselen tok for lang tid. Prøv å forenkle spørsmålet eller prøv igjen senere."
- Ingen data lagres til memory (timeout = ikke vellykket interaksjon)

**Vanlige årsaker til timeout:**
- Komplekse SQL-spørringer som tar lang tid
- DSPy Chain of Thought legger til ekstra LLM-kall
- Database cold start
- Web search (hvis aktivert)

**Løsninger:**
- Forenkle spørsmålet
- Bruke predefinerte scripts i stedet for dynamisk SQL
- Øke timeout hvis nødvendig (men vær forsiktig med UX)

---

### 2. SQL-generering feil

**DSPy SQL Generator feilhåndtering:**

| Feil-type | Håndtering | Bruker-melding |
|-----------|------------|----------------|
| Tom SQL-generering | Returnerer error | "Kunne ikke generere SQL fra spørsmålet" |
| Validering feiler | Sikkerhetsblokkering | "SQL validering feilet - ikke READ-ONLY" |
| Syntaksfeil | Database-feil med hint | "SQL-syntaksfeil. Sjekk JSONB-syntaks..." |
| Kolonne finnes ikke | Database-feil med hint | "Kolonne eller tabell finnes ikke..." |
| Operatør-feil | Database-feil med hint | "Operatør-feil. Husk å caste JSONB-verdier..." |

**Hybrid SQL-strategi:**
- Enkle spørringer → `gpt-4o-mini` (billig, rask)
- Komplekse spørringer → `gpt-4o` (høy kvalitet)
- Automatisk fallback ved feil

**Eksempel på feilhåndtering:**
```python
try:
    # Kompleksitets-deteksjon
    is_complex = self._detect_complexity(question)
    
    # Bruk riktig modell
    if is_complex:
        pred = self.generate_fallback(question=question, schema_context=schema)
    else:
        pred = self.generate_mini(question=question, schema_context=schema)
    
    clean_sql = SQLValidator.clean(pred.sql_query)
    
    if not SQLValidator.validate(clean_sql):
        return {"error": "SQL validering feilet...", "sql": clean_sql}
    
    # Retry-logikk for database-operasjoner
    result = await self._execute_with_retry(db, clean_sql)
    # ...
except Exception as db_error:
    # Gir spesifikke hints basert på feil-type
    return {"error": f"{hint} Detaljer: {error_msg}", "sql": clean_sql}
```

---

### 3. Database-tilkoblingsfeil

**Serverless Database spesielle utfordringer:**

- **Cold start**: Database kan være suspendert → `pool_pre_ping=True` håndterer dette
- **Connection timeout**: 30 sekunder (konfigurert i `session.py`)
- **Command timeout**: 60 sekunder

**Hva skjer ved database-feil:**
- Health endpoint returnerer `"db": "degraded"` (ikke "connected")
- Backend fortsetter å fungere, men database-operasjoner kan feile
- Plattformen stopper ikke tjenesten (health endpoint returnerer 200 selv ved degraded)

**Retry-strategi:**
- `pool_pre_ping=True` tester tilkoblinger før bruk
- SQLAlchemy håndterer automatisk reconnection
- ✅ **Eksplisitt retry-logikk implementert** (eksponensiell backoff: 1s, 2s, 4s)
- Maks 3 retry-forsøk ved transient errors

---

### 4. LLM-feil (Writer)

**Hva skjer hvis Writer feiler:**

```python
try:
    response = await llm.ainvoke(llm_messages)
    return {"messages": [response], ...}
except Exception as e:
    # Fallback til enkel tekst-syntese
    final_text = "Beklager, jeg klarte ikke å generere et fullstendig svar akkurat nå."
    # Prøver å hente noe fra memory hvis tilgjengelig
    return {"messages": [AIMessage(content=final_text)], ...}
```

**Vanlige årsaker:**
- API-nøkkel ugyldig/mangler
- Rate limiting
- Modell ikke tilgjengelig
- Token-limit overskredet

---

### 5. Memory-feil

**Hva skjer hvis memory-operasjoner feiler:**

- `search_memory()` feiler → Returnerer tom liste (ikke kritisk)
- `add_memory()` feiler → Logges, men chat fortsetter (ikke kritisk)
- Memory er ikke kritisk for funksjonalitet, bare for kontekst

---

### 6. Edge cases og null-sikkerhet (chat/API)

**Dokumentert oppførsel:**

| Scenario | Håndtering |
|----------|------------|
| **`chat()` kalles uten db** | Memory og tool discovery hoppes over (`if db:`); grafen kjører med tomme lister. Ingen krasj. |
| **`research_data["results"]` er enkel streng** | F.eks. fra `lookup_properties`. Normaliseres til liste før kilder-ekstraksjon slik at vi ikke itererer over tegn. |
| **API: `usage` er null** | Chat-endepunktet sjekker `usage_data` før `.get()`; ingen `AttributeError`. |

**Relevante filer:** `app/services/intelligence/ki_kollega/service.py` (chat, sources), `app/api/v1/ai/chat.py` (usage).

---

## Testing og Evaluering

### Golden Set (Test-sett)

**Anbefalt struktur for test-sett:**

```python
GOLDEN_SET = [
    {
        "question": "Gi meg den største eiendommen",
        "expected_sql_pattern": "SELECT.*total_area.*ORDER BY.*DESC.*LIMIT 1",
        "expected_route": "analyst",
        "min_result_count": 1
    },
    {
        "question": "Hvor ligger Storgata 10?",
        "expected_route": "researcher",
        "expected_tool": "lookup_properties"
    },
    {
        "question": "Hva er gjennomsnittlig leie per region?",
        "expected_sql_pattern": "AVG.*amount_per_year.*GROUP BY.*region",
        "expected_route": "analyst"
    }
]
```

**Test-kategorier:**
1. **Routing-tester**: Verifiser at Supervisor ruter korrekt
2. **SQL-generering**: Verifiser at DSPy genererer korrekt SQL
3. **JSONB-håndtering**: Test komplekse JSONB-spørringer
4. **Feilhåndtering**: Test timeout, database-feil, LLM-feil
5. **Sikkerhet**: Test Guardian blokkerer sensitive forespørsler

---

## Deployment og Infrastruktur

### Backend (Railway)

**Konfigurasjon:**
- Health endpoint: `/api/v1/health`
- Restart Policy: Always
- Replicas: 1+

**Miljøvariabler:**
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=...  # Må matche NEXTAUTH_SECRET i frontend
```

### Database (Supabase PostgreSQL)

**Serverless-egenskaper:**
- Kan suspendere ved inaktivitet
- Cold start kan ta 1-3 sekunder
- `pool_pre_ping=True` håndterer wakeup automatisk

**Connection pool:**
- `pool_size=3`
- `max_overflow=7`
- `pool_recycle=3600` (1 time)

---

## Implementerte Forbedringer (Januar 2026)

### ✅ 1. Hybrid LLM-Routing i Supervisor

**Status**: ✅ IMPLEMENTERT

**Implementering**: Kombinerer keyword-matching (rask) med LLM-klassifisering (nøyaktig)
- Bruker `gpt-4o-mini` for routing (raskere og billigere)
- Fallback til keyword-routing hvis LLM feiler
- Kan deaktiveres med `USE_HYBRID_ROUTING = False`

**Fordeler**: 
- Håndterer tvetydige spørsmål bedre
- "Oversikt over porteføljen" → Klassifiseres korrekt som "analyst"
- Reduserer feil routing

**Se**: `IMPLEMENTERTE_FORBEDRINGER.md` for detaljer

---

### ✅ 2. SQL Caching

**Status**: ✅ IMPLEMENTERT

**Implementering**: Cache for spørsmål → SQL mapping
- TTL-basert utløp (1 time)
- FIFO eviction (max 100 entries)
- Cache-statistikk (hits, misses, hit rate)

**Fordeler**:
- Reduserer LLM-kall med ~75% (cache hit rate)
- Raskere respons for ofte brukte spørsmål
- Automatisk cache-invalidering etter TTL

**Se**: `IMPLEMENTERTE_FORBEDRINGER.md` for detaljer

---

### ✅ 3. Retry-logikk for Database-operasjoner

**Status**: ✅ IMPLEMENTERT

**Implementering**: Eksponensiell backoff ved database-feil
- Maks 3 retry-forsøk (1s, 2s, 4s)
- Kun retry ved transient errors (connection, timeout)
- Ikke retry ved syntaks-feil

**Fordeler**:
- Håndterer serverless cold starts bedre
- Reduserer feilrate ved midlertidige database-problemer

**Se**: `IMPLEMENTERTE_FORBEDRINGER.md` for detaljer

---

### ✅ 4. Hybrid SQL-strategi (Fallback til gpt-4o)

**Status**: ✅ IMPLEMENTERT

**Implementering**: Automatisk valg mellom `gpt-4o-mini` og `gpt-4o` basert på kompleksitet
- Kompleksitets-deteksjon (JSONB, JOINs, aggregering)
- Proaktiv fallback (komplekse spørringer → gpt-4o direkte)
- Reaktiv fallback (gpt-4o-mini feiler → gpt-4o)

**Fordeler**:
- Kostnadseffektivitet (bruker billig modell når mulig)
- Kvalitet (bruker kraftig modell når nødvendig)
- Robusthet (fallback ved feil)

**Se**: `HYBRID_SQL_STRATEGI.md` for detaljer

---

### ✅ 5. Testing (Golden Set, Comprehensive, Integrasjon)

**Status**: ✅ IMPLEMENTERT

**Test-filer:**

| Fil | Dekker |
|-----|--------|
| `tests/test_ki_kollega_golden_set.py` | Routing, SQL-mønstre, JSONB (8+ cases). Krever DSPy cache skrivbar. |
| `tests/test_ki_kollega_comprehensive.py` | Init, chat uten db, timeout, kilder (liste/streng), verktøy, SQL-sikkerhet, proactive, API. |
| `tests/integration/test_ki_kollega_integration.py` | Init, chat timeout/success med mock. |

**DSPy cache:** `conftest.py` setter `DSPY_CACHEDIR` til `tests/.pytest_dspy_cache`. I readonly-miljø skippes golden set; comprehensive og integrasjon kjører uansett.

**Se**: `tests/README.md` og `README_KI_KOLLEGA.md` (Testing-seksjon)

---

### 🔄 Fremtidige Forbedringer

#### Streaming av status

**Forslag**: Frontend viser status underveis
```
"Analyserer spørsmålet..." → "Søker i dokumenter..." → "Genererer SQL..." → "Skriver svar..."
```

**Implementering**: LangGraph støtter streaming via `astream()`.

---

## Monitoring og Logging

### Viktige logger-punkter

1. **Supervisor routing**: Logger hvilken agent som velges
2. **SQL-generering**: Logger generert SQL (for debugging)
3. **Database-feil**: Logger SQL + feilmelding
4. **Timeout**: Logger timeout med spørsmål
5. **Usage tracking**: Logger token-bruk og kostnad

### Metrics å spore

- Gjennomsnittlig responstid per agent
- SQL-generering suksessrate
- Timeout-rate
- Database connection pool usage
- LLM token-bruk og kostnad

---

## Konklusjon

KI Kollega har solid feilhåndtering på alle nivåer:
- ✅ Timeout-håndtering med vennlige meldinger
- ✅ SQL-validering og sikkerhet
- ✅ Database-feil med spesifikke hints
- ✅ LLM-feil med fallback
- ✅ Graceful degradation (memory er ikke kritisk)

**Neste steg**: Implementer Golden Set testing og monitoring for å måle faktisk ytelse i produksjon.
