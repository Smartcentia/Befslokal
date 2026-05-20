# KI Kollega – grundig oversikt

**Hva:** Kontekstbevisst AI-assistent for BEFS Eiendom. Svarer på spørsmål om eiendommer, kontrakter, kostnader, dokumenter og lovverk ved hjelp av et agent-graf (LangGraph) og verktøy mot database, dokumenter og eksterne API-er.

**Hvor:** Frontend sender meldinger til backend `POST /api/v1/ai/chat`. Backend kjører en LangGraph-flyt (Supervisor → Guardian → Researcher → Analyst → Writer) og returnerer svar, kilder og oppfølgingsspørsmål.

---

## 1. Frontend → Backend

| Komponent | Beskrivelse |
|-----------|-------------|
| **UI** | `ChatWidget` / `ChatInterface` – bruker skriver i chat-vinduet (f.eks. «Hva er de største eiendomene i kvm?»). |
| **Klient** | `frontend/lib/domains/innsikt/kiKollegaService.ts` – `chat(message, context?, history?, conversationId?)`. Kontekst hentes fra URL (`extractContextFromPath`, f.eks. `/properties/abc-123` → `entity_type: "property"`, `entity_id: "abc-123"`). |
| **API-kall** | `fetchAPI('/ai/chat', { method: 'POST', body: JSON.stringify({ message, context, history, conversation_id, stream: false }) })`. Base-URL kommer fra `NEXT_PUBLIC_API_URL` (ingen fallback). |
| **Backend-endepunkt** | `backend/app/api/v1/ai/chat.py` – `POST /chat` mottar `ChatRequest`, konverterer til service-format, kaller `ki_kollega_service.chat(message, context, history, db)` og returnerer `ChatResponse` (answer, sources, follow_up_questions, conversation_id). |

---

## 2. Backend – innledende steg (før grafen)

I `backend/app/services/intelligence/ki_kollega/service.py` – `KIKollegaService.chat()`:

1. **OpenAI-klient**  
   Sjekkes; hvis ikke konfigurert (mangler `OPENAI_API_KEY` eller `USE_LOCAL_AI`), returneres feilmelding.

2. **Minne og persona**  
   Hvis `db` er satt:
   - `AgentMemoryService.search_memory(db, message, limit=3)` – relevante minner.
   - `AgentMemoryService.search_memory(db, "persona", …)` – persona-definisjon.
   - Tidligere samtaler (minne med `type: "conversation"`).
   Dette legges inn i kontekst som SystemMessage(er) senere.

3. **Verktøyoppdagelse**  
   `ToolDiscoveryService.find_relevant_tools(db, message, limit=2)` – søker i `AgentMemory` med `type: "tool_definition"` ved hjelp av embeddings (cosine similarity). Returnerer opp til 2 verktøy (navn, beskrivelse, parametere). Hvis ingen verktøy er registrert i minnet, blir listen tom.

4. **Query-normalisering**  
   I Supervisor og Researcher normaliseres brukerens melding før nøkkelord-sjekk: `expand_query_terms(normalize_query(message))`. Dette håndterer skrivefeil (eiendomer→eiendommer), forkortelser (fvk→familievernkontor) og synonymer (leietakere→parter, billigste per kvm→lavest kostnad per kvm). Søkeord utvides via `get_search_terms_for_property_lookup()` for eiendomssøk.

5. **Input til grafen**  
   Bygger `inputs = { "messages": [SystemMessage(memory_context?), HumanMessage(message)], "discovered_tools": discovered_tools, "persona": persona_text }` og kaller `app.ainvoke(inputs)` med timeout 45 s. `app` er den kompilerte LangGraph-flyten.

---

## 3. Agent-graf (LangGraph)

Grafen er definert i `backend/app/services/intelligence/agents/graph.py`.

**Noder:**

| Node | Fil | Rolle |
|------|-----|--------|
| **supervisor** | `nodes/supervisor.py` | Bestemmer neste steg ut fra brukerens melding: writer (hilsen/generelt), researcher (søk/dokumenter/analyse), analyst (SQL/database), eller action (systemhandlinger). Normaliserer og utvider meldingen. |
| **guardian_research** | `nodes/guardian.py` | Sikkerhetsfilter før research: blokkerer søk som inneholder f.eks. «fødselsnummer», «passord». Ved blokk: `next_step: writer` med forklaring. |
| **researcher** | `nodes/researcher.py` | Utfører søk: kjører discovered tools (search_documents, lookup_properties, run_sql_query), fulltekst/RAG, Lovdata, eller web. Returnerer SystemMessage eller ruter til analyst. |
| **analyst** | `nodes/analyst.py` | Databaseanalyse: matcher brukerens spørsmål mot faste skript eller bruker DSPy SQL Generator til å kjøre SELECT-spørringer mot PostgreSQL. Resultatet sendes til writer. |
| **action_node** | `nodes/action_node.py` | Systemhandlinger & Human-in-the-Loop: Klargjør parametere for verktøy (eks. opprette Jira-sak). Grafen pauser og returnerer `pending_action` i staten. |
| **writer** | `nodes/writer.py` | Samler brukerens spørsmål, resultater fra researcher/analyst/action, bygger en system prompt med regler, kaller OpenAI og returnerer AIMessage med endelig svar. |

**Kantflyt:**

**Kantflyt:**

- **Entry:** `supervisor`.
- **supervisor** → `guardian_research` (hvis `next_step == "researcher"`), eller → `analyst` (hvis `next_step == "analyst"`), eller → `action` (hvis handling kreves), eller → `writer`.
- **guardian_research** → `researcher` (godkjent) eller → `writer` (blokkert).
- **researcher** → `writer` (med resultater) eller → `analyst` (database-spørsmål / ingen treff) eller → `action`.
- **analyst** → `writer`.
- **action** → `writer` (returnerer for validering, setter `pending_action`).
- **writer** → END.

State (AgentState) inneholder `messages`, `next_step`, `research_data`, `discovered_tools`, `persona`, `pending_action`, `action_result`, `usage`, `error`.

---

## 4. Verktøy (tools) i KI Kollega

Definert i `ki_kollega/service.py` under `TOOLS` (OpenAI function-calling-format). Brukes av researcher (og indirekte analyst) via `ki_kollega_service._tool_*`.

| Verktøy | Beskrivelse | Implementasjon |
|---------|-------------|----------------|
| **search_documents** | Søk i dokumenter (rutiner, krav). | Embedding + hybrid/fulltext (search_hybrid / search_fulltext). Returnerer «Ingen dokumenter funnet» ved tomt resultat. |
| **run_sql_query** | Databaseanalyse (eiendommer, kontrakter, statistikk). | `_tool_run_sql` → `_handle_sql_analysis` → DSPy (sql_generator). Genererer SELECT fra naturlig språk og kjører mot DB. Schema med bl.a. `properties.total_area`. |
| **lookup_properties** | Søk eiendommer på navn, adresse eller bruk (usage). | SQL med ILIKE på `name`/`address`/`usage`. Søkeord utvides via `get_search_terms_for_property_lookup()` (fvk→familievernkontor m.m.). Returnerer «Ingen eiendommer funnet» ved tomt resultat. Brukes ikke for analyse-spørsmål («største», «kvm») – da brukes run_sql_query eller analyst. |
| **search_lovdata** | Søk i Lovdata (lover, forskrifter). | LovdataClient – ekstern API. |
| **assess_property_risk** | Risikovurdering for eiendom (NVE, Kartverket, miljø). | Henter eiendom fra DB, kaller ExternalRiskService (eller RiskAssessmentService). |

ToolDiscoveryService henter *relevante* verktøy fra AgentMemory (tool_definition + embedding). Hvis ingen verktøy er registrert der, er `discovered_tools` tom og supervisor/researcher bruker kun nøkkelord og fallbacks (fulltext, analyst, run_sql i researcher).

---

## 5. SQL og «største eiendommer i kvm»

- **Researcher:** For spørsmål med ord som «største», «kvm», «areal» brukes ikke `lookup_properties` (som søker navn/adresse). Hvis `run_sql_query` er i `discovered_tools`, kalles `_tool_run_sql(db, user_message)`; ellers rutes til analyst.
- **Analyst:** Hvis ingen faste skript treffer (`SAFE_ANALYSIS_SCRIPTS`, ~40 stk), kalles `dspy_generator.execute_query(db, original_question)`.
- **Query library:** Før DSPy genererer ny SQL, sjekkes **query_library** (tabell med 100+ lagrede SQL-mønstre fra tidligere vellykkede kjøringer). Hvis brukerens spørsmål matcher et mønster (fulltekst-søk, min. bruk og suksessrate), brukes den lagrede SQL-en direkte – raskere og mer stabilt.
- **DSPy:** Hvis ingen treff i query_library, genererer DSPy SQL fra schema (inkl. `properties.total_area`, `region`, JSONB-eksempler i SCHEMA.md) og kjører mot DB. Resultatet formateres som tabell og sendes til writer.
- **Writer:** Får SystemMessage med ANALYST_RESULT (tabell + evt. SQL). Skriver et kollegavennlig svar uten å eksponere rå «database»-termer.

---

## 6. Etter grafen – tilbake til chat()

- **Svar:** `last_msg.content` fra `final_state["messages"]` (AIMessage fra writer).
- **Kilder:** Bygges via `_extract_sources_from_state()` fra `research_data.structured_sources`, `script_results` eller legacy `results`. Hver kilde har type (property, contract, party, document, lovdata, web), name, og enten `id` (interne lenker) eller `url` (eksterne lenker). Frontend viser opptil 8 klikkbare lenker.
- **Minne:** Samtalen lagres med `AgentMemoryService.add_memory(db, chat_interaction, metadata={"type": "conversation", …})`.
- **Usage:** Hvis writer/LLM rapporterer token-bruk, kan det logges (f.eks. api_usage_tracker).

API-et returnerer dette som `ChatResponse`: answer, sources, follow_up_questions, conversation_id, evt. error og usage.

---

## 7. Avhengigheter

| Avhengighet | Bruk |
|-------------|------|
| **OPENAI_API_KEY** | OpenAI-klient (chat, embeddings, DSPy SQL-generering). |
| **Database (PostgreSQL)** | Eiendommer, kontrakter, minne, fulltext/vector-søk, SQL-kjøring. |
| **NEXT_PUBLIC_API_URL** | Frontend må ha riktig backend-URL (f.eks. `https://knowme-backend-production.up.railway.app`) – ingen fallback. |
| **SECRET_KEY / NEXTAUTH** | Autentisering for `/api/v1/ai/chat` (middleware). |
| **config/SCHEMA.md** | Brukes av DSPy for å generere SQL (tabeller, kolonner som `total_area`). |
| **query_library (tabell)** | Lagrede SQL-mønstre fra tidligere kjøringer; brukes av DSPy execute_query før LLM-generering (100+ mønstre mulig). |
| **AgentMemory (tool_definition)** | For at ToolDiscoveryService skal returnere verktøy; ellers stoler flyten på nøkkelord og analyst/researcher-logikk. |

---

## 8. Kort flyt – ett spørsmål

1. Bruker skriver i ChatInterface → `kiKollegaService.chat(message, context, history)`.
2. `fetchAPI('/ai/chat', …)` → `POST {backend}/api/v1/ai/chat`.
3. Backend: minne + persona + ToolDiscovery → `inputs` → `app.ainvoke(inputs)`.
4. **Supervisor:** Normaliserer og utvider melding (query_normalizer), leser discovered_tools → bestemmer researcher / analyst / writer.
5. **Guardian** (kun hvis researcher): Sjekker forbudte termer.
6. **Researcher:** Kjører verktøy (search_documents, lookup_properties, run_sql_query) eller fulltext/Lovdata; ved analyse-spørsmål brukes run_sql eller ruting til analyst.
7. **Analyst** (ved behov): Faste skript eller DSPy SQL → kjøring mot DB → tabell til writer.
8. **Writer:** Samler kontekst (TOOL_RESULT, ANALYST_RESULT, minne), bygger system prompt, kaller OpenAI → AIMessage.
9. Backend: Henter answer og sources fra state, lagrer samtale i minne, returnerer ChatResponse.
10. Frontend viser svar og kilder i chat-vinduet.

---

## 9. Enkel modus (kun OpenAI + data)

Når full agent-flyt ikke fungerer, kan du bruke **enkel modus** – én OpenAI-kall med **alle domenedata** i konteksten, uten LangGraph eller verktøy.

- **Backend:** `POST /api/v1/ai/chat/simple` – henter fra DB: **eiendommer**, **kontrakter**, **parter**, **enheter**, **sentre**, og **kostnad per eiendom** (vedlikehold, totalkostnad, kostnad per kvm fra external_data.financials). Alt legges i system-prompt og sendes til OpenAI én gang. Spørsmål som «hvilke eiendommer har høyest kostnad per kvm» besvares ut fra kostnadstabellen.
- **Frontend:** I chat-vinduet: avkryss **«Enkel modus (kun data + OpenAI)»**. Da brukes `chatSimple()` som kaller `/ai/chat/simple`. Valget lagres i `localStorage` (ki_kollega_simple).

### Test enkel modus nå (steg for steg)

1. Åpne KI Kollega-chatten i appen (f.eks. Innsikt / KI Kollega).
2. Nederst i chat-vinduet: **kryss av for «Enkel modus (kun data + OpenAI)»**.
3. Start eventuelt en ny samtale («Ny samtale») slik at du tester kun enkel modus.
4. Skriv f.eks. **«Hvilke eiendommer er størst i kvm?»** eller **«List opp eiendommer med mest areal»**.
5. Svar kommer fra én OpenAI-kall med alle domenedata (eiendommer, kontrakter, parter, enheter, sentre) i system-prompten – ingen agent-graf. Du kan spørre om eiendommer, kontrakter, utløpsdatoer, parter/leietakere, enheter/lokaler og sentre.

Hvis enkel modus svarer riktig, virker OpenAI + DB; da ligger problemet i full flyt (Supervisor/Researcher/Analyst). Hvis enkel modus også feiler, sjekk OPENAI_API_KEY, database-tilkobling og at du er innlogget (auth for `/api/v1/ai/chat/simple`).

---

## 10. Feilsøking

- **«Ingen eiendommer funnet» på analyse-spørsmål:** Tidligere ble `lookup_properties` kalt med hele setningen; nå hoppes den over for analyse-nøkkelord, og `run_sql_query` eller analyst brukes. Sjekk at researcher kjører run_sql/analyst og at DSPy/schema har `properties.total_area`.
- **401 på /ai/chat:** Sjekk at bruker er innlogget og at SECRET_KEY (Railway) = NEXTAUTH_SECRET (Vercel).
- **404 eller feil URL:** Sjekk at `NEXT_PUBLIC_API_URL` er satt i Vercel (f.eks. `https://knowme-backend-production.up.railway.app`) og at backend faktisk er deployet på den URL-en.
- **Tomt svar / timeout:** Sjekk OPENAI_API_KEY på Railway, og at DB og migrasjoner er OK (schema for DSPy). Se backend-logs for supervisor/researcher/analyst/writer og eventuelle Python-exceptions.

---

*Dokumentet beskriver flyten i kodebasen per i dag. Ved endringer i grafen, verktøy eller API, bør denne filen oppdateres.*
