# KI Kollega – full beskrivelse av data og funksjon

**Dokumenttype:** Samlet oversikt  
**Sist oppdatert:** Februar 2025

Dette dokumentet beskriver **hvilke data KI Kollega har tilgang til** og **hvordan systemet fungerer**. Det konsoliderer informasjon fra flere kilder til ett referansedokument.

---

## 1. Oversikt

**KI Kollega** er en kontekstbevisst AI-assistent for BEFS Eiendom. Den svarer på spørsmål om eiendommer, kontrakter, kostnader, dokumenter og lovverk.

**Fire moduser:**
- **Enkel** – én OpenAI-kall med alle domenedata i konteksten (ingen agent-graf)
- **Avansert** – LangGraph-flyt med Supervisor → Researcher/Analyst → Writer (nøkkelord-ruting)
- **Unified** – ReAct-løkke: LLM velger verktøy dynamisk (function calling). Enklere arkitektur, bedre semantisk forståelse.
- **Fullverdig** – under utvikling (placeholder)

**Autentisering:** Alle KI Kollega-endepunkter krever innlogget bruker (JWT). Se [INFORMASJONSSIKKERHET.md](INFORMASJONSSIKKERHET.md).

---

## 2. Hvordan KI Kollega fungerer (kort)

### Enkel modus
1. Bruker sender melding → `POST /api/v1/ai/chat/simple`
2. Backend henter **alle** domenedata fra databasen (ingen grense)
3. Data + BEFS-instruksjoner legges i system-prompt
4. Én OpenAI-kall → svar returneres

### Avansert modus
1. Bruker sender melding → `POST /api/v1/ai/chat` eller `/chat/stream`
2. Backend: minne, persona, verktøyoppdagelse → input til LangGraph
3. **Supervisor** ruter til researcher, analyst eller writer
4. **Guardian** (ved researcher): blokkerer søk med sensitiv informasjon
5. **Researcher** kjører verktøy (dokumenter, eiendommer, parter, SQL, Lovdata, risiko)
6. **Analyst** (ved behov): faste skript eller DSPy SQL-generering mot database
7. **Writer** samler resultater, kaller OpenAI → endelig svar
8. Svar, kilder og oppfølgingsspørsmål returneres

### Unified modus (ReAct)
1. Bruker sender melding → `POST /api/v1/ai/chat/unified`
2. **Før grafen:** Sidekontekst (BRUKEREN SER PÅ), minne og persona injiseres som Avansert
3. **Guardian** sjekker for sensitiv informasjon (fødselsnummer, passord, etc.)
4. **Agent** (LLM med verktøy) velger selv hvilke verktøy som skal brukes
5. Løkke: Agent → (tool_calls?) → Tools → Agent → (ingen tools) → END (maks 8 iterasjoner)
6. Samme verktøy som Avansert: run_sql_query, lookup_properties, lookup_parties, search_documents, search_lovdata, assess_property_risk
7. Query-normalisering i verktøy (fvk→familievernkontor, etc.)
8. Kilder hentes fra verktøy (structured_sources) og returneres i API-svar
9. DSPy brukes inni run_sql_query – SQL genereres trygt fra naturlig språk

*Implementasjon: `backend/app/services/intelligence/unified_agent/`*

*Detaljert flyt: [KI_KOLLEGA_HOW_IT_WORKS.md](KI_KOLLEGA_HOW_IT_WORKS.md)*

---

## 3. Data KI Kollega har tilgang til

### 3.1 Enkel modus – alle domenedata (én gang per forespørsel)

| Datatype | Tabell/Kilde | Kolonner/felt |
|----------|--------------|---------------|
| **Eiendommer** | `properties` | name, address, city, total_area, region |
| **Eiendommer (alle navn)** | `properties` | name, region (for «alle X», «finn alle familievernkontor») |
| **Kontrakter** | `contracts` + parties + units + properties | kategori, status, start_date, end_date, part, eiendom |
| **Parter** | `parties` | name, orgnr, contact_email, contact_phone |
| **Enheter** | `units` + properties | eiendom, formål (purpose), areal (area_sqm), etasje (floor), sone (zone_type) |
| **Sentre** | `centers` | name, description, region |
| **Kostnad per eiendom** | `properties.external_data.financials` | totalkostnad (total_manual_expenses + total_spend_csv), kostnad per kvm |

*Implementasjon: `backend/app/api/v1/ai/chat.py` – `_load_all_domain_data_for_simple_chat()`*

### 3.2 Avansert og Unified modus – verktøy (tools)

| Verktøy | Beskrivelse | Datakilde |
|---------|-------------|-----------|
| **search_documents** | Søk i dokumenter (rutiner, krav, instrukser) | `text_content` – fulltekst + vektorsøk (embedding) |
| **lookup_properties** | Søk eiendommer på navn, adresse eller bruk | `properties` – SQL ILIKE |
| **lookup_parties** | Søk parter og tilhørende kontrakter | `parties` + `contracts` – SQL med JOIN |
| **run_sql_query** | Databaseanalyse fra naturlig språk | Dynamisk SQL mot hele databasen (via DSPy) |
| **search_lovdata** | Søk i lover og forskrifter | Lovdata API (ekstern) |
| **assess_property_risk** | Risikovurdering for eiendom | NVE, Kartverket, Miljødirektoratet (eksterne API-er) |

*Implementasjon: Avansert: `backend/app/services/intelligence/ki_kollega/service.py` – TOOLS. Unified: `backend/app/services/intelligence/unified_agent/tools.py` – create_befs_tools()*

### 3.3 Analyst / DSPy – database-schema

Analyst og `run_sql_query` bruker schema fra `backend/app/config/SCHEMA.md` for å generere SQL. Tilgjengelige tabeller og felt:

| Tabell | Viktige kolonner |
|--------|------------------|
| **properties** | property_id, name, address, city, region, total_area, land_area, construction_year, energy_label, external_data (JSONB) |
| **units** | unit_id, property_id, external_data (area, usage_type) |
| **contracts** | contract_id, unit_id, party_id, status, start_date, end_date, amount (JSONB: amount_per_year, amount_per_month), filename_number |
| **parties** | party_id, name, orgnr, role |

**JSONB-felt:**
- `contracts.amount` → amount_per_year, amount_per_month
- `units.external_data` → area, usage_type
- `properties.external_data.financials` → total_manual_expenses, total_spend_csv, transactions_2024

*Schema: [backend/app/config/SCHEMA.md](../backend/app/config/SCHEMA.md)*

### 3.4 Dokumenter (search_documents)

- **Kilde:** `text_content` (PostgreSQL)
- **Innhold:** Chunked tekst fra dokumenter (rutiner, krav, kontrakter, instrukser)
- **Søk:** Fulltekst (norwegian) + evt. hybrid (embedding + fulltekst)
- **Metadata:** source_file, source_type, category, contract_id, property_id, unit_id

### 3.5 Eksterne API-er

| API | Bruk | Data |
|-----|------|------|
| **Lovdata** | search_lovdata | Lover, forskrifter, paragrafer – offentlige juridiske dokumenter |
| **NVE** | assess_property_risk | Flomfare, flomsone, avstand til vann |
| **Kartverket** | assess_property_risk | Grunnforhold, geoteknisk risiko |
| **Miljødirektoratet** | assess_property_risk | Miljørisiko |

*Web-søk (DuckDuckGo) kan brukes av researcher for generelle spørsmål – ikke BEFS-spesifikke.*

---

## 4. Brukerroller og tilgangskontroll

**Viktig:** KI Kollega har **ikke** rollebasert filtrering av data. Alle innloggede brukere får tilgang til **samme data** via KI Kollega.

| Rolle | Tilgang i resten av BEFS | Tilgang via KI Kollega |
|-------|--------------------------|-------------------------|
| **ADMIN** | Alt | Alt (som alle andre) |
| **REGIONAL_MANAGER** | Eiendommer i sin region | **Alt** – ingen regionfiltrering |
| **PROPERTY_MANAGER** | Kun tildelte eiendommer | **Alt** – ingen eiendomfiltrering |
| **TENANT** | Kun tildelte eiendommer, lesing | **Alt** – ingen begrensning |

*Dette betyr at en PROPERTY_MANAGER eller TENANT kan stille spørsmål som gir svar om eiendommer de ikke har tilgang til i resten av appen. Vurder å implementere rollefiltrering i fremtiden.*

---

## 5. Hva som er blokkert

### 5.1 Guardian (sikkerhetsfilter)

Før researcher kjører søk, sjekker **Guardian** brukerens melding for forbudte termer:

| Forbudt term | Handling |
|--------------|----------|
| fødselsnummer | Blokkert – Writer får forklaring |
| ssn | Blokkert |
| kontonummer | Blokkert |
| passord | Blokkert |

*Implementasjon: `backend/app/services/intelligence/agents/nodes/guardian.py`*

### 5.2 SQL-validering

- Kun **SELECT**-spørringer tillatt
- DROP, DELETE, INSERT, UPDATE, ALTER osv. blokkeres
- DSPy SQL Generator + SQLValidator sikrer read-only tilgang

### 5.3 Data som ikke eksponeres

- **Personnummer** – ikke i databasen som KI Kollega bruker; Guardian blokkerer søk
- **Passord** – ikke tilgjengelig; Guardian blokkerer søk
- **API-nøkler** – kun miljøvariabler, ikke i DB

---

## 6. Sikkerhetstiltak

| Tiltak | Beskrivelse |
|--------|-------------|
| **Autentisering** | Alle endepunkter krever JWT (unntatt åpne paths) |
| **Guardian** | Blokkerer søk etter sensitiv informasjon |
| **SQL-validering** | Kun read-only spørringer |
| **Debug-endepunkt** | Skjult i produksjon (`ENVIRONMENT=production`) |
| **CORS** | Begrenset til tillatte origins |

*Se [INFORMASJONSSIKKERHET.md](INFORMASJONSSIKKERHET.md) for full oversikt.*

---

## 7. Avhengigheter

| Avhengighet | Bruk |
|-------------|------|
| **OPENAI_API_KEY** | Chat, embeddings, DSPy SQL-generering |
| **PostgreSQL (Supabase)** | Eiendommer, kontrakter, parter, enheter, text_content, AgentMemory |
| **config/SCHEMA.md** | DSPy for SQL-generering |
| **query_library** (tabell) | Cache av vellykkede SQL-mønstre (100+), brukes før DSPy |
| **AgentMemory** | Minne, persona, tool_definition (verktøyoppdagelse) |
| **befs_instruksjoner.txt** | Terminologi, synonymer, regler for svar |

---

## 8. Kryssreferanser

| Dokument | Innhold |
|----------|---------|
| [KI_KOLLEGA_HOW_IT_WORKS.md](KI_KOLLEGA_HOW_IT_WORKS.md) | Detaljert flyt, steg for steg |
| [KI_KOLLEGA_TEKNISK_GJENNOMGANG.md](KI_KOLLEGA_TEKNISK_GJENNOMGANG.md) | Arkitektur, API, agenter, konfigurasjon |
| [KI_KOLLEGA_TRE_MODUSER.md](KI_KOLLEGA_TRE_MODUSER.md) | Enkel, Avansert, Fullverdig |
| [KI_KOLLEGA_EKSEMPELSPORSMAL.md](KI_KOLLEGA_EKSEMPELSPORSMAL.md) | Eksempelspørsmål |
| [INFORMASJONSSIKKERHET.md](INFORMASJONSSIKKERHET.md) | Sikkerhet, roller, autentisering |
| [BRUKERHJELP.md](BRUKERHJELP.md) | Brukerhjelp inkl. KI Kollega |

---

*Dokumentet beskriver KI Kollega per kodebasen. Ved endringer i verktøy, datakilder eller sikkerhet bør denne filen oppdateres.*
