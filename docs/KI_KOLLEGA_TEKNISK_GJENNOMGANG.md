# KI Kollega – full teknisk gjennomgang

Komplett teknisk dokumentasjon av KI Kollega: arkitektur, kodeflyt, API-er, agenter og konfigurasjon.

---

## 1. Oversikt

**KI Kollega** er en kontekstbevisst AI-assistent for BEFS Eiendom. Den svarer på spørsmål om eiendommer, kontrakter, kostnader, dokumenter og lovverk ved hjelp av:

- **Tre moduser:** Enkel (én OpenAI-kall), Avansert (LangGraph + verktøy), Fullverdig (placeholder)
- **Agent-graf:** Supervisor → Guardian → Researcher → Analyst → Writer
- **Verktøy:** Dokumenter, eiendommer, parter, Lovdata, SQL, web-søk, risikovurdering

---

## 2. Arkitektur – komponentoversikt

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND (Next.js / Vercel)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ChatInterface.tsx          → Modusvelger (Enkel|Avansert|Fullverdig)        │
│  kiKollegaService.ts        → chat(), chatStream(), chatSimple(), chatFullverdig() │
│  extractContextFromPath()   → /properties/x → entity_type, entity_id          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /api/v1/ai/chat | /chat/simple | /chat/stream | /chat/fullverdig
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ BACKEND (FastAPI / Railway)                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  chat.py                    → Router, request/response, enkel modus          │
│  ki_kollega/service.py      → KIKollegaService (chat, chat_stream, tools)     │
│  ki_kollega/query_normalizer.py → Normalisering, synonym-utvidelse, søkeord  │
│  agents/graph.py            → LangGraph: supervisor→guardian→researcher→analyst→writer │
│  agents/nodes/*.py          → Supervisor, Guardian, Researcher, Analyst, Writer │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              PostgreSQL      OpenAI API      MCP/Lovdata/Web
              (Supabase)     (gpt-4o)        (DuckDuckGo)
```

---

## 3. API-endepunkter

| Endepunkt | Metode | Beskrivelse |
|-----------|--------|-------------|
| `/api/v1/ai/chat` | POST | Avansert modus – ikke-streaming, returnerer fullt svar |
| `/api/v1/ai/chat/stream` | POST | Avansert modus – SSE-streaming av tokens |
| `/api/v1/ai/chat/simple` | POST | Enkel modus – én OpenAI-kall med alle domenedata |
| `/api/v1/ai/chat/fullverdig` | POST | Placeholder – returnerer «under utvikling» |
| `/api/v1/ai/suggestions` | GET | Kontekstbaserte forslag (entity_type, entity_id) |
| `/api/v1/ai/proactive` | GET | Proaktive innsikter basert på sidekontekst |
| `/api/v1/ai/health` | GET | Sjekk om OpenAI-klient er initialisert |
| `/api/v1/ai/debug` | GET | Diagnostikk (kun når ENVIRONMENT != production) |

**Request (ChatRequest):**
```json
{
  "message": "Hvilke eiendommer er størst i kvm?",
  "context": {
    "page": "/properties/abc-123",
    "entity_type": "property",
    "entity_id": "abc-123",
    "region": null
  },
  "conversation_id": "uuid",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "stream": false
}
```

**Response (ChatResponse):**
```json
{
  "answer": "De 10 største eiendommer etter areal er...",
  "sources": [
    {"type": "property", "id": "uuid", "name": "Storgata 12", "relevance": 0.9},
    {"type": "lovdata", "name": "Husleieloven § 5-1", "url": "https://lovdata.no/..."},
    {"type": "web", "name": "Ekstern artikkel", "url": "https://..."}
  ],
  "follow_up_questions": ["Hva er kostnaden per kvm?"],
  "query_type": "analysis",
  "conversation_id": "uuid",
  "error": null,
  "usage": {"prompt_tokens": 1200, "completion_tokens": 150, "total_tokens": 1350, "estimated_cost_usd": 0.004}
}
```

**Source-typer:** `property`, `contract`, `party` (interne lenker via `id`), `document`, `lovdata`, `web` (eksterne lenker via `url`).

---

## 4. Frontend – kodeflyt

### 4.1 ChatInterface.tsx

**Plassering:** `frontend/app/components/features/ChatInterface.tsx`

**State:**
- `mode`: `'enkel' | 'avansert' | 'fullverdig'` – lagres i `localStorage` (`ki_kollega_mode`)
- `messages`, `loading`, `conversationId`, `suggestions`, `input`

**Modusvelger:** Brukeren velger modus; ved `avansert` brukes `chatStream()`, ved `enkel` brukes `chatSimple()`, ved `fullverdig` brukes `chatFullverdig()`.

**Entity-lenker i Markdown:** ReactMarkdown har custom `components.a` som tolker:
- `property:uuid` → `<Link href="/properties/{uuid}">`
- `contract:uuid` → `<Link href="/contracts/{uuid}">`
- `party:uuid` → `<Link href="/parties/{uuid}">`

**Kilder:** Sources fra API vises som klikkbare lenker (opptil 8):
- `property`/`contract`/`party` med `id` → interne lenker til BEFS-sider
- `web`/`lovdata`/`document` med `url` → eksterne lenker (åpnes i ny fane) eller interne lenker (f.eks. `/contracts/{id}`)

**TTS:** Knapp for «Les opp» (SpeechSynthesisUtterance, `no-NO`).

### 4.2 kiKollegaService.ts

**Plassering:** `frontend/lib/domains/innsikt/kiKollegaService.ts`

```typescript
// Kontekst fra pathname
extractContextFromPath("/properties/abc-123") → { page, entity_type: "property", entity_id: "abc-123" }

// Avansert (streaming)
chatStream(message, context?, history?, conversationId?) → AsyncGenerator<{type, content?, sources?, ...}>

// Enkel
chatSimple(message, context?, history?, conversationId?) → Promise<ChatResponse>

// Fullverdig (placeholder)
chatFullverdig(...) → Promise<ChatResponse>

// Forslag
getSuggestions(entityType?, entityId?) → Promise<{suggestions: string[]}>
```

**Streaming:** Leser `fetch` body som ReadableStream, parser SSE `data:`-linjer, yield-er `{type: 'content'|'done'|'error', ...}`.

---

## 5. Backend – chat.py (router)

**Plassering:** `backend/app/api/v1/ai/chat.py`

### 5.1 Enkel modus – `_load_all_domain_data_for_simple_chat()`

Henter **alle** domenedata fra DB (ingen LIMIT):

| Tabell/Data | SQL/Funksjon |
|-------------|--------------|
| Eiendommer | `properties` (name, address, city, total_area, region) |
| Eiendommer alle navn | `properties` (name, region) – for «alle X» |
| Kontrakter | `contracts` + parties + units + properties |
| Parter | `parties` (name, orgnr, contact_email, contact_phone) |
| Enheter | `units` + properties |
| Sentre | `centers` |
| Kostnad per eiendom | `external_data.financials` (total_manual_expenses, total_spend_csv) |

Alt sendes i én system-prompt til OpenAI sammen med `befs_instruksjoner.txt` og regler for spørsmålstyper.

### 5.2 Avansert modus – `chat()` og `chat_stream()`

Videresender til `ki_kollega_service.chat()` / `chat_stream()` med konvertert context og history.

### 5.3 Suggestions

`_pick_suggestions(entity_type, limit)` – henter fra `suggestions_data.py`:
- Ved `entity_type` (property/contract/party): `SUGGESTIONS_BY_ENTITY_TYPE[entity_type]`
- Ellers: `KI_KOLLEGA_EKSEMPELSPORSMAL` (100+ spørsmål)

---

## 6. KI Kollega Service (ki_kollega/service.py)

**Plassering:** `backend/app/services/intelligence/ki_kollega/service.py`

### 6.1 Initialisering

- `USE_LOCAL_AI`: AsyncOpenAI mot `LOCAL_AI_STATION_URL`, modell `LOCAL_MODEL_NAME`
- Ellers: AsyncOpenAI med `OPENAI_API_KEY`, `OPENAI_BASE_URL`, modell `OPENAI_MODEL`

### 6.2 chat() – hovedflyt

1. **Minne:** `AgentMemoryService.search_memory(db, message, limit=3)`
2. **Persona:** `AgentMemoryService.search_memory(db, "persona", filters={"type": "persona_definition"})`
3. **BEFS-instruksjoner:** `get_befs_instruksjoner()` fra `befs_instruksjoner.txt`
4. **Tidligere samtaler:** `AgentMemoryService.search_memory(..., filters={"type": "conversation"})`
5. **Verktøy:** `ToolDiscoveryService.find_relevant_tools(db, message, limit=2)`
6. **Sidekontekst:** `_get_page_context_summary(db, context)` – kort sammendrag for property/contract/party
7. **Input til graf:** `{messages, discovered_tools, persona}`
8. **Kjør graf:** `app.ainvoke(inputs)` med timeout 45 s
9. **Etter graf:** Hent answer, sources via `_extract_sources_from_state()` (fra `research_data.structured_sources`, `script_results`, eller legacy `results`), lagre samtale i minne, logg usage

### 6.3 chat_stream()

Bruker `app.astream_events(inputs, version="v2")`, filtrerer på `on_chat_model_stream` når `in_writer` er True, yield-er tokens. Ved slutt yield-er `done` med sources.

### 6.4 Verktøy (TOOLS)

| Verktøy | Beskrivelse | Implementasjon |
|---------|-------------|----------------|
| `search_documents` | Søk i dokumenter | `_tool_search_documents` → search_hybrid/search_fulltext |
| `run_sql_query` | Databaseanalyse | `_tool_run_sql` → `_handle_sql_analysis` → DSPy |
| `lookup_properties` | Søk eiendommer | `_tool_lookup_properties` → SQL ILIKE, returnerer `{formatted, structured_sources}` |
| `lookup_parties` | Søk parter + kontrakter | `_tool_lookup_parties` → SQL med JOIN, returnerer `{formatted, structured_sources}` |
| `search_lovdata` | Lovdata-søk | `_tool_search_lovdata` → LovdataClient, returnerer `{formatted, structured_sources}` |
| `assess_property_risk` | Risikovurdering | `_tool_assess_property_risk` → ExternalRiskService |

**Lenker:** Researcher og Analyst bygger `structured_sources` (type, id, name, url) som `_extract_sources_from_state()` mapper til API-sources. Writer får instruksjon om å bruke `[Navn](property:uuid)` i svaret for klikkbare lenker.

---

## 7. Agent-graf (LangGraph)

**Plassering:** `backend/app/services/intelligence/agents/graph.py`

### 7.1 State (AgentState)

```python
messages: List[BaseMessage]      # Samtale + SystemMessages fra agenter
next_step: str                   # "researcher" | "analyst" | "writer"
current_agent: str
research_data: Dict              # results, tool, type, structured_sources
discovered_tools: List[Dict]
persona: Optional[str]
available_scripts: List[str]
script_results: Dict
error: Optional[str]
usage: Optional[Dict]
use_lovdata: Optional[bool]
```

### 7.2 Graf-flyt

```
                    ┌──────────────┐
                    │  supervisor  │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
  guardian_research    analyst           writer
         │                 │                 │
         │                 │                 │
         ▼                 │                 │
    researcher ◄───────────┘                 │
         │                                   │
         ├───────────────────────────────────┤
         │                                   │
         ▼                                   ▼
    analyst / writer ──────────────────► END
```

### 7.3 Query-normalisering (query_normalizer.py)

**Plassering:** `backend/app/services/intelligence/ki_kollega/query_normalizer.py`

Før nøkkelord-sjekk i Supervisor og Researcher normaliseres brukerens melding:

- **normalize_query():** Whitespace, lowercase, vanlige skrivefeil (eiendomer→eiendommer, familievernkontoor→familievernkontor).
- **expand_query_terms():** BEFS-synonymer (fvk→familievernkontor, leietakere→parter, billigste per kvm→lavest kostnad per kvm).
- **get_search_terms_for_property_lookup():** Returnerer liste av søkeord for eiendomssøk (f.eks. «fvk» → [familievernkontor, familievern, fvk]). Researcher prøver termer inntil treff.

### 7.4 Supervisor (supervisor.py)

**Rutelogikk (prioritet):**

Brukerens melding normaliseres og utvides via `expand_query_terms(normalize_query(raw_text))` før nøkkelord-sjekk.

1. **Hilsninger** → writer
2. **discovered_tools:** `lookup_properties`/`search_documents` → researcher; `run_sql_query` → analyst
3. **BEFS-kontrakt/part:** «har vi kontrakt med X», «leietaker Y» → researcher
4. **Eksplisitt SQL** → analyst
5. **Juridiske nøkkelord** (lov, husleie, HMS, …) → researcher, `use_lovdata=True`
6. **«Alle X»** (alle familievernkontor, fvk, barnevern, bup, hvilke er) → researcher
7. **Analyse-nøkkelord** (største, antall, kostnad, …) → analyst
8. **Søk-nøkkelord** → researcher
9. **Fallback:** Semantisk routing (embedding vs AGENT_DESCRIPTIONS) eller LLM-klassifisering

**Semantisk routing:** `_semantic_route()` – cosine similarity mellom query-embedding og agent-beskrivelser, terskel 0.65.

**LLM-routing:** `_llm_classify_intent()` – gpt-4o-mini klassifiserer til researcher/analyst/writer.

### 7.5 Guardian (guardian.py)

Sjekker siste melding for forbudte termer: `fødselsnummer`, `ssn`, `kontonummer`, `passord`. Ved treff → `next_step: writer` med forklaring, ellers → researcher.

### 7.6 Researcher (researcher.py)

Bruker `text_normalized = expand_query_terms(normalize_query(last_user_input))` for alle nøkkelord-sjekker.

**Prioritet:**

1. **Juridiske spørsmål** → `_tool_search_lovdata`, returner LOVDATA_RESULTATER
2. **«Alle X»** (alle familievernkontor, fvk, hvilke eiendommer er X, barnevern, bup) → `_tool_lookup_properties` med `get_search_terms_for_property_lookup()` (prøver flere termer ved behov), returner EIENDOMER_FUNNET
3. **«Har vi kontrakt med X»** → `_tool_lookup_parties`, returner PARTER_OG_KONTRAKTER
4. **discovered_tools** → Kjør search_documents, lookup_properties, lookup_parties, run_sql_query
5. **Fulltekst-søk** → search_fulltext
6. **Lookup (ikke analyse)** → lookup_properties
7. **Web-søk** (kun hvis IKKE database-spørsmål) → `search_web_tool`
8. **Fallback** → Rute til analyst (DATABASE_SPØRSMÅL eller INGEN_RESULTATER)

**Database vs web:** `database_query_keywords` brukes til å skille – ved analyse/sammenligninger hoppes web over, rutes til analyst.

### 7.7 Analyst (analyst.py)

**Prioritet:**

1. **DSPy-first for firma/parter** – nøkkelord: firma, part, leverandør, leietaker, hvilket, hvem
2. **Faste skript** – `SAFE_ANALYSIS_SCRIPTS` (cost_analyzer_top, audit_contracts, …)
3. **DSPy SQL Generator** – `dspy_generator.execute_query(db, question)`

**DSPy:** Self-correction ved SQL-feil (maks 2 retries med feilmelding i kontekst). Resultat formateres som tabell (maks 10 rader) og sendes til writer.

### 7.8 Writer (writer.py)

1. Samler kontekst fra SystemMessages (TOOL_RESULT, ANALYST_RESULT, LOVDATA_RESULTATER, …)
2. Bygger system prompt med persona, BEFS-instruksjoner, regler (aldri SQL/tekniske detaljer)
3. Kaller `ChatOpenAI` med `astream` for token-streaming
4. Returnerer AIMessage, usage (prompt_tokens, completion_tokens, estimated_cost)

**Regler til LLM:** Aldri vis SQL, database-spørringer eller tekniske termer; snakk som kollega; strukturer svar naturlig.

---

## 8. Støttetjenester

### 8.1 AgentMemoryService

- `add_memory(db, content, metadata)` – lagrer med embedding
- `search_memory(db, query, limit, filters)` – cosine similarity mot `AgentMemory`

### 8.2 ToolDiscoveryService

- `find_relevant_tools(db, user_query, limit)` – søker `AgentMemory` med `type: "tool_definition"`, returnerer tool_name, description, parameters

### 8.3 DSPy SQL Generator

**Plassering:** `backend/app/services/dspy/sql_generator.py`

- `TextToSQL` signature – schema_context + question → sql_query
- `SQLValidator` – blokkerer DROP, DELETE, INSERT, …
- `query_library` – cache av vellykkede SQL-mønstre (100+)
- Schema fra `config/SCHEMA.md` med JSONB-eksempler

### 8.4 MCP Handler

**Plassering:** `backend/app/services/mcp/handler.py`

- `search_documents_tool` – search_fulltext
- `search_web_tool` – DuckDuckGo-søk (brukes av researcher, due_diligence, company_summary)

### 8.5 BEFS-instruksjoner

**Plassering:** `backend/app/services/intelligence/ki_kollega/befs_instruksjoner.txt`

- Terminologi: leietakere = parter, familievernkontor, billigste eiendom per kvm
- Eksempler på svar
- Regler: svar på norsk, telling = eksakt tall, «alle X» = list alle

---

## 9. Konfigurasjon

| Miljøvariabel | Bruk |
|---------------|------|
| `OPENAI_API_KEY` | OpenAI-klient (påkrevd for avansert/enkel) |
| `OPENAI_MODEL` | Modell (f.eks. gpt-4o) |
| `OPENAI_BASE_URL` | Valgfri base-URL |
| `USE_LOCAL_AI` | Bruk Local AI Station |
| `LOCAL_AI_STATION_URL` | URL til lokal modell |
| `LOCAL_MODEL_NAME` | Modellnavn ved lokal AI |
| `ENVIRONMENT` | `production` skjuler /ai/debug |

---

## 10. Filer – oversikt

| Fil | Rolle |
|-----|-------|
| `frontend/app/components/features/ChatInterface.tsx` | UI, modusvelger, entity-lenker, TTS |
| `frontend/lib/domains/innsikt/kiKollegaService.ts` | API-klient, streaming, context |
| `backend/app/api/v1/ai/chat.py` | Router, enkel modus, suggestions |
| `backend/app/api/v1/ai/suggestions_data.py` | 100+ eksempelspørsmål |
| `backend/app/services/intelligence/ki_kollega/service.py` | Hovedservice, chat, tools |
| `backend/app/services/intelligence/ki_kollega/befs_instruksjoner.txt` | Terminologi og regler |
| `backend/app/services/intelligence/agents/graph.py` | LangGraph-definisjon |
| `backend/app/services/intelligence/agents/state.py` | AgentState |
| `backend/app/services/intelligence/agents/nodes/supervisor.py` | Rutelogikk |
| `backend/app/services/intelligence/agents/nodes/guardian.py` | Sikkerhetsfilter |
| `backend/app/services/intelligence/agents/nodes/researcher.py` | Verktøy, Lovdata, web |
| `backend/app/services/intelligence/agents/nodes/analyst.py` | Skript, DSPy SQL |
| `backend/app/services/intelligence/agents/nodes/writer.py` | LLM-syntese |
| `backend/app/services/dspy/sql_generator.py` | SQL-generering |
| `backend/app/services/mcp/handler.py` | MCP-verktøy, search_web_tool |
| `backend/app/services/agent_memory_service.py` | Minne |
| `backend/app/services/tool_discovery_service.py` | Verktøyoppdagelse |
| `backend/app/main.py` | `include_router(ki_kollega_router, prefix="/api/v1/ai")` |

---

## 11. Forbedring: «største eiendommer med lav husleie»

For at KI Kollega skal svare på slike spørsmål:

1. **SCHEMA.md:** `contracts.status` bruker `'active'` (ikke 'Aktiv'). DSPy genererer SQL fra schema.
2. **Analysis keywords:** «lav», «billig», «lav husleie» ruter til Analyst (supervisor + researcher).
3. **Query library:** Kjør seed for å legge inn bevist SQL:
   ```bash
   cd backend && python scripts/seed_query_library_storste_lav_husleie.py
   ```

---

## 12. Feilsøking

| Symptom | Mulig årsak |
|---------|-------------|
| 401 på /ai/chat | SECRET_KEY ≠ NEXTAUTH_SECRET, eller bruker ikke innlogget |
| «Client not initialized» | OPENAI_API_KEY mangler |
| Timeout | CHAT_TIMEOUT_SECONDS=45; forenkle spørsmål eller sjekk DB/OpenAI |
| «Ingen eiendommer funnet» på analyse | Researcher ruter feil; sjekk at analyst/DSPy får spørsmålet |
| Tomt svar fra writer | Sjekk at researcher/analyst returnerer gyldig kontekst |
| Enkel modus fungerer, avansert ikke | Problem i graf (supervisor/researcher/analyst); sjekk logs |

---

*Dokumentet beskriver KI Kollega per kodebasen. Ved endringer bør denne filen oppdateres.*
