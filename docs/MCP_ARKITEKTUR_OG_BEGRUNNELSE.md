# Model Context Protocol (MCP) – Arkitektur og Begrunnelse

## Innholdsfortegnelse
1. [Hva er MCP?](#hva-er-mcp)
2. [Hvorfor valgte vi MCP?](#hvorfor-valgte-vi-mcp)
3. [Hvordan fungerer MCP i vår løsning?](#hvordan-fungerer-mcp-i-vår-løsning)
4. [Arkitektur og implementasjon](#arkitektur-og-implementasjon)
5. [Konkrete eksempler](#konkrete-eksempler)
6. [Fordeler og gevinster](#fordeler-og-gevinster)

---

## Hva er MCP?

**Model Context Protocol (MCP)** er en standardisert protokoll for AI-systemer som fungerer som en **Enterprise Service Bus (ESB) for AI**. Det er en åpen standard som gjør det mulig for AI-agenter å kommunisere med eksterne verktøy, tjenester og datakilder på en strukturert og sikker måte.

### Kjernekonsepter

MCP definerer tre hovedkomponenter:

1. **Tools (Verktøy)** – Funksjoner som AI-agenten kan kalle
2. **Resources (Ressurser)** – Data som AI-agenten kan lese
3. **Prompts (Maler)** – Forhåndsdefinerte instruksjoner

I BEFS bruker vi primært **Tools** for å gi KI Kollega tilgang til spesialiserte funksjoner.

---

## Hvorfor valgte vi MCP?

### 1. **Standardisering og Interoperabilitet**

Før MCP hadde vi to alternativer:
- **Hardkode alle funksjoner** direkte i AI-agenten → ufleksibelt, vanskelig å vedlikeholde
- **Bygge egne integrasjoner** for hver tjeneste → duplikasjon, inkonsistens

MCP gir oss:
- ✅ **Én standard** for alle verktøy
- ✅ **Gjenbrukbare komponenter** på tvers av agenter
- ✅ **Enklere testing** av individuelle verktøy
- ✅ **Bedre separasjon** mellom AI-logikk og forretningslogikk

### 2. **Dynamisk verktøyoppdagelse**

Med MCP kan KI Kollega:
- **Oppdage tilgjengelige verktøy** ved oppstart
- **Velge riktig verktøy** basert på brukerens spørsmål
- **Legge til nye verktøy** uten å endre AI-agentens kjernekode

Dette gjøres via `ToolDiscoveryService`:

```python
# KI Kollega finner automatisk relevante verktøy
discovered_tools = await ToolDiscoveryService.find_relevant_tools(
    db, 
    user_query="Hvilke eiendommer har vi i Oslo?", 
    limit=2
)
# Resultat: ["lookup_properties", "execute_sql_query"]
```

### 3. **Sikkerhet og kontroll**

MCP-verktøy har:
- **Validering** av input-parametere (via Pydantic schemas)
- **Rate limiting** (f.eks. SQL-verktøyet: maks 10 queries/minutt)
- **Read-only enforcement** (SQL-verktøyet blokkerer DROP, DELETE, INSERT)
- **Audit logging** av alle verktøykall

### 4. **Skalerbarhet og vedlikehold**

Ved å bruke MCP kan vi:
- **Legge til nye integrasjoner** (Jira, Unit4, Mapbox) uten å endre AI-agenten
- **Oppdatere verktøy** uavhengig av hverandre
- **Teste verktøy** isolert fra resten av systemet
- **Gjenbruke verktøy** i flere agenter (KI Kollega, Due Diligence Agent, Company Summary Agent)

---

## Hvordan fungerer MCP i vår løsning?

### Overordnet arkitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                         KI KOLLEGA                               │
│                    (LangGraph Agent System)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Kaller verktøy via MCP Handler
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP HANDLER                                 │
│              (backend/app/services/mcp/handler.py)               │
│                                                                  │
│  • Registrerer alle verktøy                                      │
│  • Validerer input                                               │
│  • Håndterer async/sync execution                                │
│  • Returnerer strukturerte resultater                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
    ┌────────┐     ┌──────────┐    ┌─────────┐   ┌──────────┐
    │Database│     │ Lovdata  │    │ Mapbox  │   │ Web Søk  │
    │  Tools │     │   API    │    │   API   │   │ (DuckGo) │
    └────────┘     └──────────┘    └─────────┘   └──────────┘
```

### MCP Handler – Kjernekomponent

[MCPHandler](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/mcp/handler.py) er hjerte i MCP-implementasjonen:

```python
class MCPHandler:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}

    def register_tool(self, name: str, description: str, parameters: Dict):
        """Decorator for å registrere et verktøy"""
        def decorator(func: Callable):
            self._tools[name] = func
            self._definitions[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters
            )
            return func
        return decorator

    async def execute_tool(self, name: str, arguments: Dict, db=None):
        """Kjør et verktøy med validering og feilhåndtering"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        
        func = self._tools[name]
        # Håndter både async og sync funksjoner
        if inspect.iscoroutinefunction(func):
            return await func(**arguments)
        else:
            return await run_in_threadpool(func, **arguments)
```

### Registrering av verktøy

Hvert verktøy registreres med `@mcp_handler.register_tool`:

```python
@mcp_handler.register_tool(
    name="lookup_properties",
    description="Søk etter eiendommer basert på navn, adresse eller region",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Søkeord"}
        },
        "required": ["query"]
    }
)
async def lookup_properties_tool(query: str, db=None):
    async with get_or_use_session(db) as session:
        # Søk i database
        result = await session.execute(
            select(Property).where(Property.name.ilike(f"%{query}%"))
        )
        properties = result.scalars().all()
        
        # Returner strukturert data
        return {
            "formatted": f"Fant {len(properties)} eiendommer...",
            "structured_sources": [
                {"type": "property", "id": str(p.property_id), "name": p.name}
                for p in properties
            ]
        }
```

---

## Arkitektur og implementasjon

### 1. MCP Handler (`handler.py`)

**Plassering:** [backend/app/services/mcp/handler.py](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/mcp/handler.py)

**Ansvar:**
- Registrere alle verktøy
- Validere input-parametere
- Håndtere async/sync execution
- Returnere strukturerte resultater

**Antall verktøy:** 50+ registrerte verktøy (se [fullstendig liste](#fullstendig-verktøyliste))

### 2. MCP Service (`mcp_service.py`)

**Plassering:** [backend/app/services/mcp_service.py](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/mcp_service.py)

**Ansvar:**
- Kommunikasjon med eksterne MCP-servere
- Gateway-integrasjon (Docker MCP Gateway)
- Remote server management

```python
class MCPService:
    def __init__(self):
        self.gateway_url = settings.DOCKER_MCP_GATEWAY_URL
        self._remote_servers = self._load_remote_servers()

    async def list_tools(self) -> List[Dict]:
        """List tools from Gateway + Remote Servers"""
        all_tools = []
        
        # 1. Local Gateway
        response = await self._client.get(f"{self.gateway_url}/tools")
        all_tools.extend(response.json()["tools"])
        
        # 2. Remote Servers (Lovdata, Jira, etc.)
        for name, url in self._remote_servers.items():
            response = await self._client.get(f"{url}/tools")
            all_tools.extend(response.json()["tools"])
        
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict):
        """Route tool call to correct server"""
        if server_name in self._remote_servers:
            return await self._call_direct(url, tool_name, arguments)
        return await self._call_gateway(server_name, tool_name, arguments)
```

### 3. MCP API Endpoints

**Plassering:** [backend/app/api/v1/mcp/](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/api/v1/mcp/)

Vi har spesialiserte MCP-servere for ulike domener:

| MCP Server | Beskrivelse | Verktøy |
|------------|-------------|---------|
| **GDPR** | Personvernkontroll | `check_gdpr_compliance`, `anonymize_data` |
| **Risk** | Risikovurdering | `assess_property_risk`, `calculate_risk_score` |
| **Document** | Dokumenthåndtering | `search_documents`, `extract_text` |
| **Fulltext** | Fulltekstsøk | `search_fulltext` (PostgreSQL FTS) |
| **Action** | Arbeidsordre | `create_work_order`, `list_actions` |
| **Finans** | Økonomisk analyse | `get_financial_summary`, `compare_costs` |
| **BIM** | Bygningsinformasjon | `get_building_components`, `check_ns3451` |
| **FDV** | Drift og vedlikehold | `get_maintenance_plan`, `schedule_inspection` |
| **IoT** | Sensorer og målinger | `get_sensor_data`, `check_energy_usage` |
| **Memory** | Agent-minne | `search_memory`, `add_memory` |

### 4. Tool Discovery Service

**Plassering:** [backend/app/services/tool_discovery_service.py](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/tool_discovery_service.py)

Bruker **semantisk søk** for å finne relevante verktøy:

```python
class ToolDiscoveryService:
    @staticmethod
    async def find_relevant_tools(db, user_query: str, limit: int = 2):
        """Find tools using semantic search in AgentMemory"""
        results = await AgentMemoryService.search_memory(
            db=db,
            query=user_query,
            limit=limit,
            filters={"type": "tool_definition"}
        )
        
        return [
            {
                "tool_name": r.metadata.get("tool_name"),
                "description": r.metadata.get("description"),
                "parameters": r.metadata.get("parameters")
            }
            for r in results
        ]
```

**Eksempel:**
```
User: "Hvilke eiendommer har vi i Oslo?"
→ Discovered tools: ["lookup_properties", "execute_sql_query"]

User: "Hva sier husleieloven om depositum?"
→ Discovered tools: ["search_lovdata", "search_documents"]
```

---

## Konkrete eksempler

### Eksempel 1: Eiendomssøk

**Brukerens spørsmål:** "Hvilke familievernkontor har vi?"

**Flyt:**

1. **Supervisor** ruter til **Researcher** (nøkkelord: "hvilke", "familievernkontor")
2. **Researcher** normaliserer query: `"familievernkontor"` → `["familievernkontor", "familievern", "fvk"]`
3. **Researcher** kaller MCP-verktøy:
   ```python
   result = await mcp_handler.execute_tool(
       name="lookup_properties",
       arguments={"query": "familievernkontor"},
       db=db
   )
   ```
4. **MCP Handler** kjører `lookup_properties_tool`:
   ```python
   # Søker i database
   properties = await db.execute(
       select(Property).where(Property.name.ilike("%familievernkontor%"))
   )
   
   # Returnerer strukturert data
   return {
       "formatted": "Fant 12 familievernkontor:\n- FVK Oslo\n- FVK Bergen\n...",
       "structured_sources": [
           {"type": "property", "id": "uuid-1", "name": "FVK Oslo"},
           {"type": "property", "id": "uuid-2", "name": "FVK Bergen"}
       ]
   }
   ```
5. **Writer** formaterer svaret med klikkbare lenker:
   ```markdown
   Vi har 12 familievernkontor:
   - [FVK Oslo](property:uuid-1)
   - [FVK Bergen](property:uuid-2)
   ```

### Eksempel 2: SQL-analyse

**Brukerens spørsmål:** "Hva er gjennomsnittlig kostnad per kvm for våre eiendommer?"

**Flyt:**

1. **Supervisor** ruter til **Analyst** (nøkkelord: "gjennomsnittlig", "kostnad", "kvm")
2. **Analyst** kaller MCP-verktøy:
   ```python
   result = await mcp_handler.execute_tool(
       name="execute_sql_query",
       arguments={
           "query": """
               SELECT 
                   AVG((external_data->'financials'->>'total_costs')::numeric / total_area) as avg_cost_per_sqm
               FROM properties
               WHERE total_area > 0
           """
       },
       db=db
   )
   ```
3. **MCP Handler** validerer SQL (read-only, rate limit OK)
4. **MCP Handler** kjører query og returnerer resultat
5. **Writer** formaterer: "Gjennomsnittlig kostnad er 1,234 kr/kvm"

### Eksempel 3: Lovdata-søk

**Brukerens spørsmål:** "Hva sier husleieloven om depositum?"

**Flyt:**

1. **Supervisor** ruter til **Researcher** med `use_lovdata=True`
2. **Researcher** kaller MCP-verktøy:
   ```python
   result = await mcp_handler.execute_tool(
       name="search_lovdata",
       arguments={"query": "husleieloven depositum"}
   )
   ```
3. **MCP Handler** kaller `LovdataClient`:
   ```python
   async def search_lovdata_tool(query: str):
       client = LovdataClient()
       results = await client.search(query, limit=3)
       
       return {
           "formatted": "Relevante lovbestemmelser:\n- Husleieloven § 3-5...",
           "structured_sources": [
               {
                   "type": "lovdata",
                   "name": "Husleieloven § 3-5",
                   "url": "https://lovdata.no/dokument/NL/lov/1999-03-26-17/§3-5"
               }
           ]
       }
   ```
4. **Writer** inkluderer Lovdata-referanser i svaret

---

## Fullstendig verktøyliste

Her er alle MCP-verktøy registrert i systemet:

### Database og søk
- `search_documents` – Søk i dokumenter (PostgreSQL FTS)
- `search_fulltext` – Avansert fulltekstsøk med norsk språkstøtte
- `execute_sql_query` – Kjør read-only SQL-spørringer
- `lookup_properties` – Søk eiendommer
- `lookup_parties` – Søk parter og kontrakter
- `search_contracts` – Søk i kontrakter
- `list_properties` – List eiendommer med filtrering
- `list_contracts` – List kontrakter med finansielle detaljer
- `get_property_info` – Hent detaljert eiendomsinformasjon

### Analyse og beregning
- `classify_risk` – Risikoklassifisering
- `assess_property_risk` – Beregn risiko for eiendom
- `check_anomalies` – Sjekk for avvik
- `compare_contracts_by_price` – Sammenlign kontrakter på pris
- `calculate_days_between` – Beregn dager mellom datoer
- `check_leap_year` – Sjekk om skuddår

### Arbeidsordre og HMS
- `create_work_order` – Opprett arbeidsordre
- `check_internal_control` – Sjekk internkontroll-status

### Eksterne tjenester
- `search_lovdata` – Søk i Lovdata
- `search_web_tool` – Web-søk (DuckDuckGo)
- `fetch_web_content_tool` – Hent innhold fra URL
- `get_nearby_services` – Finn nærliggende tjenester (Mapbox)
- `fetch_ssb_market_data` – Hent markedsdata fra SSB

### Dokumentasjon og hjelp
- `list_help_articles` – List hjelpedokumenter
- `read_help_article` – Les hjelpedokument
- `read_audit_logs` – Les revisjonslogger

### Kodeanalyse
- `execute_code` – Kjør Python-kode (sandboxed)
- `run_analysis_script` – Kjør forhåndsdefinerte analyseskript

---

## Fordeler og gevinster

### 1. **Modularitet**

Hvert verktøy er en selvstendig modul som kan:
- Testes isolert
- Oppdateres uavhengig
- Gjenbrukes på tvers av agenter
- Dokumenteres separat

### 2. **Sikkerhet**

MCP gir oss:
- **Input-validering** via Pydantic schemas
- **Rate limiting** for å forhindre misbruk
- **Read-only enforcement** for SQL-verktøy
- **Audit logging** av alle verktøykall
- **Error handling** med strukturerte feilmeldinger

### 3. **Skalerbarhet**

Vi kan enkelt:
- **Legge til nye verktøy** uten å endre AI-agenten
- **Integrere eksterne tjenester** (Jira, Unit4, Mapbox)
- **Opprette spesialiserte MCP-servere** for ulike domener
- **Distribuere verktøy** på tvers av flere servere

### 4. **Vedlikeholdbarhet**

MCP gjør kodebasen:
- **Lettere å forstå** (klart skille mellom AI og forretningslogikk)
- **Enklere å debugge** (verktøy kan testes isolert)
- **Tryggere å endre** (verktøy har klare grensesnitt)
- **Bedre dokumentert** (hver tool har beskrivelse og parameter-schema)

### 5. **Fleksibilitet**

Med MCP kan vi:
- **Bytte ut implementasjoner** uten å endre grensesnittet
- **A/B-teste** ulike verktøy-implementasjoner
- **Gradvis migrere** til nye tjenester
- **Støtte flere backends** (lokal, cloud, hybrid)

---

## Konklusjon

**Model Context Protocol (MCP)** er en fundamental arkitektonisk beslutning i BEFS som gir oss:

✅ **Standardisering** – Én protokoll for alle verktøy  
✅ **Sikkerhet** – Validering, rate limiting, audit logging  
✅ **Skalerbarhet** – Enkel å legge til nye integrasjoner  
✅ **Vedlikeholdbarhet** – Klar separasjon av ansvar  
✅ **Fleksibilitet** – Støtte for både lokale og eksterne tjenester  

Ved å bruke MCP har vi bygget et **robust, skalerbart og vedlikeholdbart** AI-system som kan vokse med virksomhetens behov uten å måtte omskrive kjernelogikken.

---

## Referanser

- [MCP Handler Implementation](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/mcp/handler.py)
- [MCP Service Implementation](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/mcp_service.py)
- [Tool Discovery Service](file:///Users/frank/Documents/BEFS_CLEAN/backend/app/services/tool_discovery_service.py)
- [KI Kollega Technical Documentation](file:///Users/frank/Documents/BEFS_CLEAN/docs/KI_KOLLEGA_TEKNISK_GJENNOMGANG.md)
- [Research Document](file:///Users/frank/Documents/BEFS_CLEAN/forskning.md)
