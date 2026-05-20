# KI Kollega – grundig vurdering

Dato: 2026-02-01  
Omfang: Arkitektur, flyt, verktøy, kontekst, feilhåndtering, sikkerhet, testing og anbefalinger.

---

## 1. Oppsummering

KI Kollega er en multi-agent AI-assistent bygget med **LangGraph** som svarer på spørsmål om eiendommer, kontrakter, parter og dokumenter. Vurderingen viser at **kjerneflyten er solid** (Supervisor → Guardian → Researcher → Analyst → Writer), med gode dokumenter, timeout-håndtering og BEFS-terminologi. Det er likevel **viktige mangler**: sidekontekst (entity_type/entity_id) brukes ikke i avansert modus, søk på kontraktnavn mangler, og ToolDiscoveryService er avhengig av at verktøy er registrert i AgentMemory. En konkret feil (Writer som ikke tok inn «PARTER_OG_KONTRAKTER») er rettet i denne vurderingen.

**Anbefaling:** Prioriter å injisere sidekontekst i grafen, legge til lookup/søk på kontraktnavn, og sikre at Writer og Researcher er fullt dekket av tester for nye prefikser/verktøy.

---

## 2. Arkitektur og flyt

### 2.1 Oversikt

```
Bruker (ChatInterface) → POST /api/v1/ai/chat
    → KIKollegaService.chat(message, context, history, db)
        → Henter memories, persona, BEFS-instruksjoner, discovered_tools
        → Bygger messages (history + siste spørsmål)
        → inputs = { messages, discovered_tools, persona }   ← context sendes IKKE med
        → app.ainvoke(inputs)  [LangGraph, timeout 45s]
            → SUPERVISOR (ruting)
            → GUARDIAN (sikkerhet, kun ved researcher)
            → RESEARCHER (dokumenter, lookup_properties, lookup_parties, Lovdata, fulltext, run_sql)
            → ANALYST (scripts eller DSPy SQL)
            → WRITER (syntese til bruker)
        → Returnerer answer, sources, usage
```

**Styrker:**
- Tydelig separasjon av roller (ruting, sikkerhet, søk, analyse, skriving).
- BEFS-instruksjoner (`befs_instruksjoner.txt`) lastes inn og brukes både i enkel og avansert modus.
- Timeout på 45 sekunder begrenser hengende forespørsler.
- Feil i grafen (timeout, error i state) gir brukervenlige meldinger.

**Oppdatert:** Sidekontekst er nå tatt i bruk. Når brukeren er på en kontrakt-, part- eller eiendomsside, hentes et kort sammendrag (`_get_page_context_summary`) og legges inn som en SystemMessage («BRUKEREN SER PÅ: …») øverst i meldingslisten før grafen kjøres. Writer gjenkjenner prefikset «BRUKEREN SER PÅ» og inkluderer det i konteksten til LLM.

---

## 3. Kontekst og sideinformasjon

### 3.1 Frontend

- `extractContextFromPath(pathname)` gir korrekt `ChatContext` for `/properties/[id]`, `/contracts/[id]`, `/parties/[id]`.
- `kiKollegaService.chat()` kaller med `context` når den ikke er satt (hentet fra `window.location.pathname`).
- API-et mottar og mapper `request.context` til service-format.

### 3.2 Backend

- `chat()` mottar `context: ChatContext` men bruker den **kun** i:
  - `get_proactive_insights()` (f.eks. utløpende kontrakter for `context.entity_type == "property"`).
  - Eventuell usage-tracking (`context.user_id`).
**Implementert:** Sidekontekst injiseres nå i `chat()`: ved `context.entity_type` og `context.entity_id` kalles `_get_page_context_summary(db, context)` som henter kontrakt (med part og eiendom), part (med antall kontrakter) eller eiendom (navn og adresse). Resultatet legges inn som SystemMessage «BRUKEREN SER PÅ: …» øverst i `chat_messages` før grafen kjøres. Writer inkluderer «BRUKEREN SER PÅ» i kontekst-prefiksene og gir det videre til LLM.

---

## 4. Verktøy og dekning

### 4.1 Tilgjengelige verktøy (service.py)

| Verktøy | Beskrivelse | Brukes i Researcher |
|--------|-------------|----------------------|
| `search_documents` | Søk i dokumenter (RAG/hybrid) | Ja (discovered_tools) |
| `run_sql_query` | SQL via DSPy | Ja (discovered_tools + fallback) |
| `lookup_properties` | Eiendommer på navn/adresse | Ja (alle X, discovered_tools, fallback) |
| `lookup_parties` | Parter på navn/orgnr + kontrakter | Ja (kontrakt/part-nøkkelord + discovered_tools) |
| `search_lovdata` | Lovdata (juridisk) | Ja (use_lovdata / legal_keywords) |
| `assess_property_risk` | Risikovurdering eiendom | I TOOLS, ikke eksplisitt i Researcher-branch |

**Styrker:**
- «Har vi kontrakt med X» / «leietaker Y» rutes nå til researcher og bruker `lookup_parties` (BEFS-data, ikke Lovdata).
- Tidlig branch for kontrakt/part (0.6) + discovered_tools støtte for `lookup_parties`.
- Writer får nå også resultater med prefikset «PARTER_OG_KONTRAKTER» (rettet i denne vurderingen).

**Svakheter:**
**Implementert:** Global søk (`/global?q=`) er utvidet til å søke også i `Contract.external_data['contract_name']` (JSONB), slik at kontrakter kan finnes på avtalenavn (f.eks. «F3 ungdom Nybøvegen 24»).
- ToolDiscoveryService henter verktøy fra **AgentMemory** (type `tool_definition`). Hvis `lookup_parties` ikke er registrert der, vil ikke «semantisk match» i Supervisor finne det (men keyword-ruting og Researcher 0.6 dekker det likevel).
- `assess_property_risk` er definert men få brukt i Researcher; kan være bevisst (brukes via andre kanaler).

---

## 5. Routing (Supervisor)

### 5.1 Prioritet

1. Hilsninger → writer  
2. Discovered tools (lookup_properties, search_documents → researcher; run_sql_query → analyst)  
3. **BEFS kontrakt/part** («har vi kontrakt», «kontrakt med », «leietaker», «part », «leverandør ») → researcher  
4. Eksplisitt SQL/database → analyst  
5. Juridiske nøkkelord (lov, husleieloven, kontraktsrett, …) → researcher + use_lovdata  
6. «Alle X» → researcher  
7. Analyse-nøkkelord (største, antall, kostnad, …) → analyst  
8. Søk-nøkkelord → researcher  
9. Default: LLM-klassifisering (hybrid) eller researcher  

**Styrker:**
- «Kontrakt» er fjernet fra rent juridiske nøkkelord, så «har vi kontrakt med Pir» går til BEFS-data.
- Hybrid routing med LLM (gpt-4o-mini) ved uklare spørsmål.

**Svakheter:**
- Keyword-lister er hardkodet; nye domeneuttrykk krever kodeendring.
- LLM-routing krever OPENAI_API_KEY; ved mangler fallback til researcher (akseptabelt).

---

## 6. Researcher

### 6.1 Rekkefølge

1. Lovdata (ved use_lovdata eller juridiske nøkkelord)  
2. «Alle X» → lookup_properties  
3. **«Har vi kontrakt med X» / leietaker/part** → lookup_parties (søkeord ut fra regex)  
4. Discovered tools (search_documents, lookup_properties, lookup_parties, run_sql_query)  
5. Fulltext-søk, deretter lookup_properties ved søk-uttrykk  
6. Web search (hvis ikke database-spørsmål)  
7. Fallback: ruting til analyst (SQL)  

**Styrker:**
- Tydelig prioritering og fallback til analyst.
- lookup_parties brukes både i egen branch og i discovered_tools.

**Svakheter:**
- Regex for å trekke ut partnavn («Pir», «Acme») kan mislykkes ved uvanlige formuleringer; flere mønstre eller en enkel LLM-ekstraksjon kan stramme inn.
- SessionLocal() brukes inne i Researcher; db sesjon fra chat() brukes ikke her. Det er konsistent med andre verktøy, men pool/timing kan påvirkes ved høy last.

---

## 7. Writer

### 7.1 Kontekst-innsamling

Writer samler SystemMessages som inneholder blant annet:
- TOOL_RESULT  
- **PARTER_OG_KONTRAKTER** (lagt til i denne vurderingen – tidligere ble resultat fra lookup_parties-branch 0.6 ignorert)  
- DOKUMENTER_FUNNET, EIENDOMER_FUNNET, WEB_RESULTATER, LOVDATA_RESULTATER, ANALYST_RESULT, DATABASE_RAPPORT  
- ANALYST_FEIL, INGEN_RESULTATER  

**Styrker:**
- Klar regel om å ikke returnere rå data; svar skal være kollegiale og forklarende.
- BEFS-instruksjoner inkludert i system-prompt.
- Hilsning uten kontekst gir rask, enkel respons.

---

## 8. Feilhåndtering og timeout

- **Chat:** 45 s timeout; bruker får melding om at forespørselen tok for lang tid.
- **SQL:** DSPy + validering (kun SELECT/WITH); feil returneres til Writer som får mulighet til å formulere svar.
- **Database:** Retry med backoff dokumentert; health kan returnere «degraded».
- **LLM/Writer:** Ved feil returneres fallback-melding; krasj unngås.
- **Memory/tool discovery:** Feil logges; chat fortsetter uten memory/discovered tools.

Dokumentasjon i KI_KOLLEGA_ARKITEKTUR.md er god og i tråd med koden.

---

## 9. Sikkerhet

- **Guardian:** Blokkerer forespørsler som inneholder blant annet «fødselsnummer», «ssn», «kontonummer», «passord» og sender bruker til Writer med forklaring.
- **SQL:** Kun lese-spørringer (validering); DROP/DELETE/INSERT blokkeres i _execute_safe_sql.
- **Lovdata/eksterne API-er:** Brukes lesende; ingen brukerdata sendes ut i søkene utover selve spørsmålsteksten.

For en intern BEFS-assistent er nivået rimelig; utvidelse av Guardian (f.eks. PII-deteksjon) kan vurderes ved behov.

---

## 10. Testing

- **test_ki_kollega_comprehensive.py:** Init, timeout, kilder, verktøy (lookup_properties, run_sql), SQL-sikkerhet, proactive, API (health, suggestions, chat).
- **test_ki_kollega_integration.py:** Init, timeout, chat success med mock.
- **test_ki_kollega_golden_set.py:** Routing, SQL-mønstre (kan kreve DSPy/DB).
- **test_supervisor_routing.py:** Sannsynligvis routing-logikk.

**Implementert:** I `test_ki_kollega_comprehensive.py` er lagt til: `test_tool_lookup_parties_empty`, `test_tool_lookup_parties_short_term`, og `test_writer_includes_parter_og_kontrakter_in_prompt` (Writer inkluderer PARTER_OG_KONTRAKTER i LLM-kallet). TOOLS-listen testes også for å inneholde `lookup_parties`.

---

## 11. Dokumentasjon

- **KI_KOLLEGA_ARKITEKTUR.md:** God oversikt over flyt, feilhåndtering, timeout, testing, deployment.
- **README_KI_KOLLEGA.md:** Komplett oversikt og testinstruksjoner.
- **docs/KI_KOLLEGA_*.md:** Moduser, eksempelspørsmål, hvordan det fungerer.
- **befs_instruksjoner.txt:** Kort og tydelig terminologi og regler.

Dokumentasjonen er sterk. Sidekontekst brukes nå i avansert modus (sammendrag injiseres som «BRUKEREN SER PÅ»). Kontraktnavn-søk er implementert i global søk via `external_data.contract_name`.

---

## 12. Konkrete endringer gjort i denne vurderingen

1. **Writer:** Lagt til «PARTER_OG_KONTRAKTER» som prefiks i kontekst-innsamling, slik at resultater fra Researcher sin tidlige lookup_parties-branch (0.6) inngår i Writer sin kontekst. Uten dette ble svaret for «har vi kontrakt med Pir» ikke basert på partsøket.

---

## 13. Anbefalinger (prioritert)

| Prioritet | Tiltak |
|-----------|--------|
| Høy | **Injisere sidekontekst i grafen:** Legg `context` (entity_type, entity_id, page) i AgentState og inputs; ved contract/party/property – hent aktuelle data og gi som kontekst til Writer. |
| Høy | **Søk på kontraktnavn:** Enten utvide global søk til å inkludere external_data/contract_name, eller legge til et verktøy «lookup_contracts» (navn/tittel) som Researcher kan bruke. |
| Medium | **Tester for lookup_parties og Writer:** Enhetstest for _tool_lookup_parties; test at Writer bruker SystemMessage med «PARTER_OG_KONTRAKTER». |
| Medium | **Registrere lookup_parties i ToolDiscoveryService:** Hvis verktøy lagres i AgentMemory, legg inn tool_definition for lookup_parties slik at semantisk discovery også finner det. |
| Lav | **Forbedre navneekstraksjon:** Ved «kontrakt med X» – vurdere flere regex-mønstre eller en enkel LLM-ekstraksjon for mer robust søkeord. |
| Lav | **Dokumentere kontekst:** Oppdatert i KI_KOLLEGA_GRUNDIG_VURDERING.md at sidekontekst nå brukes (BRUKEREN SER PÅ) og at global søk inkluderer kontraktnavn. |

---

## 14. Hvordan teste (uten localhost)

Backend kjører på deployt URL; frontend bruker `NEXT_PUBLIC_API_URL` mot den. Ingen localhost.

**Automatiske tester (pytest, lokalt):**
```bash
cd backend
python3 -m pytest tests/test_ki_kollega_comprehensive.py -v
```

**Manuell testing mot deployt backend:** Backend krever `Authorization: Bearer <JWT>` for alle endepunkter unntatt `/api/v1/health`. Sett backend-URL og token:

```bash
# Backend-URL (uten /api/v1) og JWT (hent fra appen etter innlogging – DevTools → Network → Authorization header)
export BEFS_API_URL="https://api.example.com"
export BEFS_AUTH_TOKEN="<din-jwt>"

# Åpent endepunkt (krever ikke auth)
curl -s "$BEFS_API_URL/api/v1/health" | python3 -m json.tool

# KI Kollega og søk (krever auth)
curl -s -H "Authorization: Bearer $BEFS_AUTH_TOKEN" "$BEFS_API_URL/api/v1/ai/health" | python3 -m json.tool
curl -s -H "Authorization: Bearer $BEFS_AUTH_TOKEN" "$BEFS_API_URL/api/v1/search/global?q=Nybøvegen" | python3 -m json.tool
curl -s -X POST -H "Authorization: Bearer $BEFS_AUTH_TOKEN" "$BEFS_API_URL/api/v1/ai/chat" \
  -H "Content-Type: application/json" -d '{"message": "Hei"}' | python3 -m json.tool
```

**Skript:** `scripts/test_ki_kollega_api.sh` (kjør fra prosjektrot). Med token: `BEFS_API_URL=... BEFS_AUTH_TOKEN=... ./scripts/test_ki_kollega_api.sh`. Uten token får du 401 på /api/v1/ai/* og /api/v1/search/*.

**I appen (frontend):** Frontend henter alltid API-URL fra `NEXT_PUBLIC_API_URL` (Vercel/miljø). Åpne KI Kollega på en kontrakt-/part-/eiendomsside og still spørsmål; sidekontekst og «har vi kontrakt med X» testes der.

---

## 15. Konklusjon

KI Kollega er **godt bygget** med tydelig arkitektur, fornuftig feilhåndtering og god dokumentasjon. De viktigste forbedringene er **å bruke sidekontekst** (contract/party/property) i avansert modus og **å støtte søk på kontraktnavn**. Rettelsen av Writer (PARTER_OG_KONTRAKTER) sikrer at «har vi kontrakt med X» får korrekt datagrunnlag. Med de anbefalte tiltakene vil løsningen bli mer kontekstbevisst og fullere i dekning av BEFS-behov.
