# BEFS/KNOWME - Arkitekturdiagrammer

**Dokumenttype:** Arkitekturdiagrammer  
**Versjon:** 1.0  
**Dato:** 12. februar 2026  
**Målgruppe:** Arkitekter, tekniske beslutningstakere

---

## Innholdsfortegnelse

1. [Systemkontekst-diagram](#1-systemkontekst-diagram)
2. [Container-diagram](#2-container-diagram)
3. [Komponent-diagram - Backend](#3-komponent-diagram---backend)
4. [Komponent-diagram - Frontend](#4-komponent-diagram---frontend)
5. [AI Agent Workflow](#5-ai-agent-workflow)
6. [Dataflyt-diagram](#6-dataflyt-diagram)
7. [Deployment-arkitektur](#7-deployment-arkitektur)
8. [Sikkerhetsarkitektur](#8-sikkerhetsarkitektur)
9. [Integrasjonsarkitektur](#9-integrasjonsarkitektur)

---

## 1. Systemkontekst-diagram

Dette diagrammet viser BEFS/KNOWME i kontekst med eksterne systemer og brukere.

```mermaid
graph TB
    subgraph "Brukere"
        User[Eiendomsforvalter]
        Admin[Administrator]
        Economist[Økonomiansvarlig]
    end
    
    BEFS[BEFS/KNOWME<br/>Eiendomsforvaltningssystem]
    
    subgraph "Eksterne Systemer"
        OpenAI[OpenAI<br/>GPT-4o, Embeddings]
        Mapbox[Mapbox<br/>Kart og Geokoding]
        Lovdata[Lovdata<br/>Juridisk Database]
        BRREG[Brønnøysundregistrene<br/>Bedriftsinformasjon]
        NVE[NVE<br/>Flomvarsel]
        Kartverket[Kartverket<br/>Geokoding]
        Bufdir[Bufdir.no<br/>Eiendomsdata]
        Jira[Jira<br/>Arbeidsordre]
        Resend[Resend<br/>E-post og MFA]
    end
    
    User -->|Administrerer eiendommer<br/>Stiller spørsmål til KI| BEFS
    Admin -->|Konfigurerer system<br/>Administrerer brukere| BEFS
    Economist -->|Analyserer økonomi<br/>Lager budsjett| BEFS
    
    BEFS -->|LLM requests<br/>Embeddings| OpenAI
    BEFS -->|Kartvisning<br/>Geokoding| Mapbox
    BEFS -->|Juridisk søk| Lovdata
    BEFS -->|Bedriftsoppslag| BRREG
    BEFS -->|Flomdata| NVE
    BEFS -->|Adresseoppslag| Kartverket
    BEFS -->|Eiendomsimport| Bufdir
    BEFS -->|Arbeidsordre| Jira
    BEFS -->|E-post varsler<br/>MFA-koder| Resend
    
    style BEFS fill:#2563eb,color:#fff,stroke:#1e40af,stroke-width:3px
    style User fill:#10b981,color:#fff
    style Admin fill:#f59e0b,color:#fff
    style Economist fill:#8b5cf6,color:#fff
    style OpenAI fill:#10b981,color:#fff
    style Mapbox fill:#3b82f6,color:#fff
    style Lovdata fill:#ef4444,color:#fff
```

### Beskrivelse

**BEFS/KNOWME** er det sentrale systemet som:
- Håndterer eiendomsforvaltning, kontrakter og økonomi
- Tilbyr AI-assistent (KI-Kollega) for naturlig språk-interaksjon
- Integrerer med 9 eksterne systemer for berikelse av data

---

## 2. Container-diagram

Dette diagrammet viser de viktigste containerene i BEFS-arkitekturen.

```mermaid
graph TB
    User[Bruker<br/>Eiendomsforvalter]
    
    subgraph "BEFS Platform"
        Web[Web Application<br/>Next.js 14 App Router<br/>React, TypeScript, Tailwind]
        API[API Backend<br/>FastAPI<br/>Python 3.11, Async]
        AI[AI Engine<br/>LangGraph + OpenAI<br/>Multi-agent System]
        MCP[MCP Handler<br/>Tool Registry<br/>50+ verktøy]
        DB[(Database<br/>PostgreSQL 15<br/>pgvector)]
        Cache[(Redis Cache<br/>Query Results<br/>Session Data)]
    end
    
    subgraph "Eksterne Tjenester"
        OpenAI_API[OpenAI API<br/>GPT-4o]
        Mapbox_API[Mapbox API<br/>Kart]
        Lovdata_API[Lovdata API<br/>Juridisk]
        Email[Resend API<br/>E-post]
    end
    
    User -->|HTTPS| Web
    Web -->|REST API<br/>JSON| API
    API -->|SQL Queries| DB
    API -->|Cache Get/Set| Cache
    API -->|Chat Request| AI
    AI -->|Tool Execution| MCP
    MCP -->|Data Access| DB
    MCP -->|External Calls| Mapbox_API
    MCP -->|Legal Search| Lovdata_API
    AI -->|LLM Calls| OpenAI_API
    API -->|Send Email| Email
    
    style Web fill:#000,color:#fff
    style API fill:#4f46e5,color:#fff
    style AI fill:#8b5cf6,color:#fff
    style MCP fill:#10b981,color:#fff
    style DB fill:#3b82f6,color:#fff
    style Cache fill:#f59e0b,color:#fff
```

### Container-beskrivelser

| Container | Teknologi | Ansvar |
|-----------|-----------|--------|
| **Web Application** | Next.js 14, React, TypeScript | SPA med SSR, brukergrensesnitt |
| **API Backend** | FastAPI, Python 3.11 | RESTful API, forretningslogikk |
| **AI Engine** | LangGraph, OpenAI | Multi-agent AI-system |
| **MCP Handler** | Python | Tool registry og execution |
| **Database** | PostgreSQL 15 + pgvector | Persistent lagring, vektorsøk |
| **Cache** | Redis | Session cache, query results |

---

## 3. Komponent-diagram - Backend

Dette diagrammet viser backend-komponentene i detalj.

```mermaid
graph TB
    subgraph "API Layer"
        Router[FastAPI Router]
        Auth[Auth Middleware<br/>JWT Verification]
        RateLimit[Rate Limiter<br/>SlowAPI]
    end
    
    subgraph "Domain Layer"
        CoreDomain[Core Domain<br/>Properties, Units<br/>Contracts, Parties]
        HMSDomain[HMS Domain<br/>Risk, Deviations<br/>Checklists]
        FDVDomain[FDV Domain<br/>Components<br/>Maintenance]
        InnsiktDomain[Innsikt Domain<br/>Analytics<br/>Search]
    end
    
    subgraph "Service Layer"
        Intelligence[Intelligence Services<br/>KI-Kollega, Agents]
        MCPService[MCP Service<br/>Tool Registry]
        External[External Services<br/>API Integrations]
        RiskService[Risk Service<br/>Assessment]
        Analytics[Analytics Service<br/>Reporting]
        Search[Search Service<br/>Fulltext, Vector]
    end
    
    subgraph "Data Layer"
        ORM[SQLAlchemy ORM<br/>Async]
        Migrations[Alembic<br/>Migrations]
        Models[Database Models<br/>50+ tables]
    end
    
    subgraph "Infrastructure"
        DB[(PostgreSQL<br/>pgvector)]
        Cache[(Redis)]
        FileStorage[File Storage<br/>S3-compatible]
    end
    
    Router --> Auth
    Auth --> RateLimit
    RateLimit --> CoreDomain
    RateLimit --> HMSDomain
    RateLimit --> FDVDomain
    RateLimit --> InnsiktDomain
    
    CoreDomain --> Intelligence
    CoreDomain --> MCPService
    HMSDomain --> RiskService
    InnsiktDomain --> Analytics
    InnsiktDomain --> Search
    
    Intelligence --> MCPService
    MCPService --> External
    
    CoreDomain --> ORM
    HMSDomain --> ORM
    FDVDomain --> ORM
    InnsiktDomain --> ORM
    
    ORM --> Models
    Models --> DB
    Migrations --> DB
    
    Intelligence --> Cache
    Search --> Cache
    
    style Router fill:#4f46e5,color:#fff
    style Intelligence fill:#8b5cf6,color:#fff
    style MCPService fill:#10b981,color:#fff
    style DB fill:#3b82f6,color:#fff
```

### Komponent-beskrivelser

**API Layer:**
- Router: Endpoint-routing og request handling
- Auth Middleware: JWT-validering og autorisasjon
- Rate Limiter: DDoS-beskyttelse

**Domain Layer (DDD):**
- Core: Kjernedomene (eiendommer, kontrakter)
- HMS: Helse, miljø og sikkerhet
- FDV: Forvaltning, drift og vedlikehold
- Innsikt: Analyse og søk

**Service Layer:**
- Intelligence: AI-agenter og KI-Kollega
- MCP Service: Tool registry og execution
- External: Eksterne API-integrasjoner
- Risk: Risikovurdering
- Analytics: Rapportering og analyse
- Search: Fulltekstsøk og vektorsøk

---

## 4. Komponent-diagram - Frontend

Dette diagrammet viser frontend-komponentene.

```mermaid
graph TB
    subgraph "App Router"
        Layout[Root Layout<br/>Global providers]
        Dashboard[Dashboard Page<br/>Oversikt]
        Properties[Properties Pages<br/>Eiendomsliste<br/>Detaljer]
        Contracts[Contracts Pages<br/>Kontraktsliste]
        Financials[Financials Pages<br/>Økonomianalyse]
        Risk[Risk Pages<br/>Risikovurdering]
        Lab[Lab Page<br/>AI Eksperimentering]
    end
    
    subgraph "Components"
        UI[UI Components<br/>Shadcn/ui<br/>Buttons, Forms, etc.]
        Maps[Map Components<br/>Mapbox GL JS<br/>PropertyMap]
        Charts[Chart Components<br/>Recharts<br/>Visualisering]
        Forms[Form Components<br/>React Hook Form<br/>Zod validation]
        Chat[Chat Components<br/>KI-Kollega UI<br/>Message list]
    end
    
    subgraph "State Management"
        ReactQuery[React Query<br/>Server State<br/>API caching]
        Context[React Context<br/>Global UI State<br/>Theme, Locale]
        NextAuth[NextAuth<br/>Session State<br/>User auth]
    end
    
    subgraph "API Integration"
        APIClient[API Client<br/>Fetch wrapper<br/>Error handling]
        Hooks[Custom Hooks<br/>useProperties<br/>useContracts, etc.]
    end
    
    Layout --> Dashboard
    Layout --> Properties
    Layout --> Contracts
    Layout --> Financials
    Layout --> Risk
    Layout --> Lab
    
    Dashboard --> UI
    Dashboard --> Charts
    Properties --> Maps
    Properties --> UI
    Contracts --> UI
    Contracts --> Forms
    Financials --> Charts
    Lab --> Chat
    
    Dashboard --> ReactQuery
    Properties --> ReactQuery
    Contracts --> ReactQuery
    
    ReactQuery --> APIClient
    APIClient --> Hooks
    
    Layout --> NextAuth
    Layout --> Context
    
    style Layout fill:#000,color:#fff
    style ReactQuery fill:#ef4444,color:#fff
    style NextAuth fill:#10b981,color:#fff
    style APIClient fill:#3b82f6,color:#fff
```

---

## 5. AI Agent Workflow

Dette diagrammet viser KI-Kollega's multi-agent workflow.

```mermaid
graph TB
    Start([User Query]) --> Service[KIKollegaService]
    
    Service --> Memory{Hent Memory<br/>Semantic Search}
    Service --> Persona{Hent Persona<br/>User preferences}
    Service --> Tools{Discover Tools<br/>MCP Handler}
    Service --> Context{Side Context<br/>Current entity}
    
    Memory --> Graph[LangGraph Workflow]
    Persona --> Graph
    Tools --> Graph
    Context --> Graph
    
    Graph --> Supervisor{Supervisor Node<br/>Route query}
    
    Supervisor -->|Security check| Guardian[Guardian Node<br/>Block sensitive?]
    Supervisor -->|Document search| Researcher[Researcher Node<br/>Search docs/web]
    Supervisor -->|Data analysis| Analyst[Analyst Node<br/>Generate SQL]
    
    Guardian -->|Blocked| Writer[Writer Node<br/>Synthesize response]
    Guardian -->|Allowed| Researcher
    
    Researcher --> MCPTools{MCP Tools}
    Analyst --> MCPTools
    
    MCPTools -->|lookup_properties| DB[(Database)]
    MCPTools -->|search_documents| FullText[Fulltext Search]
    MCPTools -->|search_lovdata| Lovdata[Lovdata API]
    MCPTools -->|search_web| DuckDuckGo[DuckDuckGo]
    MCPTools -->|execute_sql| SQLGen[DSPy SQL Generator]
    
    SQLGen --> Validate{SQL Validator<br/>Read-only?}
    Validate -->|Valid| DB
    Validate -->|Invalid| Error[Error Response]
    
    DB --> Results[Query Results]
    FullText --> Results
    Lovdata --> Results
    DuckDuckGo --> Results
    Error --> Results
    
    Results --> Writer
    Researcher --> Writer
    Analyst --> Writer
    
    Writer --> LLM[OpenAI GPT-4o<br/>Response generation]
    LLM --> Response[Final Response<br/>+ Sources]
    
    Response --> SaveMemory{Save to Memory<br/>AgentMemoryService}
    SaveMemory --> End([Return to User])
    
    style Service fill:#3b82f6,color:#fff
    style Graph fill:#8b5cf6,color:#fff
    style Supervisor fill:#f59e0b,color:#fff
    style Guardian fill:#ef4444,color:#fff
    style Researcher fill:#10b981,color:#fff
    style Analyst fill:#06b6d4,color:#fff
    style Writer fill:#8b5cf6,color:#fff
    style MCPTools fill:#10b981,color:#fff
```

### Agent-roller

| Agent | Trigger | Ansvar | Output |
|-------|---------|--------|--------|
| **Supervisor** | Alltid først | Ruter spørsmål til riktig agent | Agent name |
| **Guardian** | Sensitive spørsmål | Blokkerer upassende forespørsler | Pass/Block |
| **Researcher** | "Finn", "Søk", "Hva er" | Søker i dokumenter, web, Lovdata | Documents + sources |
| **Analyst** | "Hvor mange", "Gjennomsnitt", "Topp 10" | Genererer og kjører SQL | Query results + SQL |
| **Writer** | Alltid sist | Syntetiserer svar fra agenter | Final response |

---

## 6. Dataflyt-diagram

### 6.1 Bruker Logger Inn

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant NextAuth
    participant Backend
    participant Database
    
    User->>Frontend: Åpner login-side
    Frontend->>User: Viser login-skjema
    
    User->>Frontend: Sender credentials
    Frontend->>NextAuth: signIn(credentials)
    
    NextAuth->>Backend: POST /api/v1/sessions/verify
    Note over NextAuth,Backend: {email, password}
    
    Backend->>Database: SELECT user WHERE email=?
    Database-->>Backend: User data + hashed password
    
    Backend->>Backend: Verify password (bcrypt)
    
    alt Password valid
        Backend->>Backend: Generate JWT token
        Backend-->>NextAuth: {token, user}
        NextAuth->>NextAuth: Create session cookie
        NextAuth-->>Frontend: Session established
        Frontend->>Frontend: Redirect to /dashboard
        Frontend-->>User: Dashboard page
    else Password invalid
        Backend-->>NextAuth: 401 Unauthorized
        NextAuth-->>Frontend: Error
        Frontend-->>User: "Feil brukernavn eller passord"
    end
```

### 6.2 Bruker Stiller Spørsmål til KI-Kollega

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant KIKollega
    participant LangGraph
    participant MCP
    participant Database
    participant OpenAI
    
    User->>Frontend: "Hvilke eiendommer har vi i Oslo?"
    Frontend->>API: POST /api/v1/ai/chat
    Note over Frontend,API: {message, entity_type, entity_id}
    
    API->>KIKollega: chat(message, user_id, db)
    
    KIKollega->>Database: Search memory (semantic)
    Database-->>KIKollega: Previous context
    
    KIKollega->>Database: Discover tools (MCP)
    Database-->>KIKollega: [lookup_properties, execute_sql]
    
    KIKollega->>LangGraph: Start workflow
    
    LangGraph->>LangGraph: Supervisor routes to Researcher
    LangGraph->>MCP: Execute tool: lookup_properties
    MCP->>Database: SELECT * FROM properties WHERE city ILIKE '%Oslo%'
    Database-->>MCP: [Property1, Property2, ...]
    MCP-->>LangGraph: Results + structured sources
    
    LangGraph->>LangGraph: Writer synthesizes response
    LangGraph->>OpenAI: Generate response
    Note over LangGraph,OpenAI: Context + results + instructions
    OpenAI-->>LangGraph: Generated text
    
    LangGraph-->>KIKollega: Final response + sources
    
    KIKollega->>Database: Save to agent_memory
    
    KIKollega-->>API: Response + usage + sources
    API-->>Frontend: JSON response
    Frontend-->>User: Display response with clickable sources
```

### 6.3 Budsjett Genereres

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant BudgetService
    participant Database
    participant Analytics
    
    User->>Frontend: Klikk "Generer budsjett"
    Frontend->>API: POST /api/v1/financials/generate-budget
    Note over Frontend,API: {property_id, year, method}
    
    API->>BudgetService: generate_budget(property_id, year)
    
    BudgetService->>Database: Hent historiske kostnader
    Note over BudgetService,Database: SELECT * FROM gl_transactions<br/>WHERE property_id=? AND year IN (year-1, year-2)
    Database-->>BudgetService: Historical data
    
    BudgetService->>Analytics: Beregn gjennomsnitt per kategori
    Analytics-->>BudgetService: Average per category per month
    
    BudgetService->>BudgetService: Apply inflation (2%)
    BudgetService->>BudgetService: Round to nearest 1000
    
    BudgetService->>Database: INSERT INTO budget (12 rows)
    Note over BudgetService,Database: One row per month
    Database-->>BudgetService: Success
    
    BudgetService-->>API: Budget created
    API-->>Frontend: {budget_id, total_amount}
    Frontend-->>User: "Budsjett opprettet: 1.2M NOK"
```

---

## 7. Deployment-arkitektur

```mermaid
graph TB
    subgraph "User Devices"
        Browser[Web Browser<br/>Desktop/Mobile]
    end
    
    subgraph "Vercel Edge Network"
        CDN[Global CDN<br/>Edge Caching]
        EdgeFunc[Edge Functions<br/>Middleware]
        NextApp[Next.js Application<br/>SSR/RSC]
    end
    
    subgraph "Railway Cloud"
        LoadBalancer[Load Balancer<br/>HTTPS]
        API1[FastAPI Instance 1<br/>Auto-scaled]
        API2[FastAPI Instance 2<br/>Auto-scaled]
        Worker[Background Worker<br/>Cron Jobs]
    end
    
    subgraph "Supabase Serverless"
        Primary[(Primary Database<br/>PostgreSQL 15)]
        Replica[(Read Replica<br/>Auto-scaled)]
    end
    
    subgraph "External Services"
        OpenAI[OpenAI API<br/>GPT-4o]
        Mapbox[Mapbox API]
        Resend[Resend Email]
    end
    
    Browser -->|HTTPS| CDN
    CDN --> EdgeFunc
    EdgeFunc --> NextApp
    
    NextApp -->|API Calls<br/>HTTPS| LoadBalancer
    LoadBalancer --> API1
    LoadBalancer --> API2
    
    API1 -->|Write| Primary
    API2 -->|Write| Primary
    API1 -->|Read| Replica
    API2 -->|Read| Replica
    Worker -->|Read/Write| Primary
    
    API1 --> OpenAI
    API2 --> OpenAI
    API1 --> Mapbox
    API2 --> Mapbox
    Worker --> Resend
    
    style CDN fill:#000,color:#fff
    style NextApp fill:#000,color:#fff
    style LoadBalancer fill:#4f46e5,color:#fff
    style API1 fill:#4f46e5,color:#fff
    style API2 fill:#4f46e5,color:#fff
    style Primary fill:#8b5cf6,color:#fff
    style Replica fill:#a78bfa,color:#fff
```

### Deployment-detaljer

| Komponent | Platform | Skalering | Region |
|-----------|----------|-----------|--------|
| **Frontend** | Vercel | Auto (Edge) | Global CDN |
| **Backend** | Railway | Auto | EU West |
| **Database** | Supabase | Auto | EU West |
| **Cache** | Redis (planned) | Manual | EU West |

---

## 8. Sikkerhetsarkitektur

```mermaid
graph TB
    subgraph "Security Layers"
        Transport[Transport Security<br/>TLS 1.3, HTTPS]
        Auth[Authentication<br/>JWT + MFA]
        Authz[Authorization<br/>RBAC]
        Input[Input Validation<br/>Pydantic Schemas]
        Output[Output Sanitization<br/>XSS Prevention]
    end
    
    subgraph "Threat Protection"
        RateLimit[Rate Limiting<br/>SlowAPI]
        CSRF[CSRF Protection<br/>SameSite Cookies]
        SQLInj[SQL Injection<br/>ORM + Parameterized]
        XSS[XSS Protection<br/>React Auto-escape]
    end
    
    subgraph "Data Protection"
        Encryption[Data Encryption<br/>At Rest + In Transit]
        GDPR[GDPR Compliance<br/>Anonymization]
        Audit[Audit Logging<br/>All sensitive ops]
        Backup[Backup<br/>Daily + PITR]
    end
    
    subgraph "Access Control"
        MFA[Multi-Factor Auth<br/>Email OTP]
        Session[Session Management<br/>JWT with expiry]
        Roles[Role-Based Access<br/>User/Admin/Super]
    end
    
    Transport --> Auth
    Auth --> MFA
    Auth --> Session
    Session --> Authz
    Authz --> Roles
    
    Input --> SQLInj
    Input --> XSS
    Output --> XSS
    
    RateLimit --> CSRF
    
    Encryption --> GDPR
    GDPR --> Audit
    Audit --> Backup
    
    style Transport fill:#10b981,color:#fff
    style Auth fill:#3b82f6,color:#fff
    style Encryption fill:#8b5cf6,color:#fff
    style MFA fill:#f59e0b,color:#fff
```

### Sikkerhetslag

1. **Transport**: TLS 1.3, HTTPS everywhere
2. **Autentisering**: JWT tokens med MFA
3. **Autorisasjon**: Role-based access control
4. **Input-validering**: Pydantic schemas på alle endpoints
5. **Rate limiting**: DDoS-beskyttelse
6. **Data-kryptering**: At rest og in transit
7. **Audit logging**: Alle sensitive operasjoner

---

## 9. Integrasjonsarkitektur

```mermaid
graph TB
    subgraph "BEFS Core"
        API[FastAPI Backend]
        MCP[MCP Handler<br/>Tool Registry]
    end
    
    subgraph "AI Services"
        OpenAI[OpenAI API<br/>GPT-4o, Embeddings]
        DSPy[DSPy<br/>SQL Generation]
    end
    
    subgraph "Mapping Services"
        Mapbox[Mapbox API<br/>Maps, Geocoding]
        Kartverket[Kartverket<br/>Address lookup]
    end
    
    subgraph "Legal & Compliance"
        Lovdata[Lovdata API<br/>Legal database]
        BRREG[Brønnøysundregistrene<br/>Company info]
    end
    
    subgraph "Risk & Environment"
        NVE[NVE API<br/>Flood warnings]
        SSB[SSB API<br/>Market data]
    end
    
    subgraph "Communication"
        Resend[Resend API<br/>Email delivery]
        Jira[Jira API<br/>Work orders]
    end
    
    subgraph "Data Sources"
        Bufdir[Bufdir.no<br/>Property data]
        Unit4[Unit4 ERP<br/>Accounting]
    end
    
    API --> MCP
    
    MCP -->|LLM calls| OpenAI
    MCP -->|SQL generation| DSPy
    DSPy --> OpenAI
    
    MCP -->|Geocoding| Mapbox
    MCP -->|Address lookup| Kartverket
    
    MCP -->|Legal search| Lovdata
    MCP -->|Company lookup| BRREG
    
    MCP -->|Flood data| NVE
    MCP -->|Market data| SSB
    
    API -->|Send email| Resend
    API -->|Create issue| Jira
    
    API -->|Import properties| Bufdir
    API -.->|Planned| Unit4
    
    style API fill:#4f46e5,color:#fff
    style MCP fill:#10b981,color:#fff
    style OpenAI fill:#10b981,color:#fff
    style Mapbox fill:#3b82f6,color:#fff
    style Lovdata fill:#ef4444,color:#fff
    style Unit4 fill:#94a3b8,color:#000
```

### Integrasjonsmønstre

| Tjeneste | Mønster | Retry | Timeout | Cache |
|----------|---------|-------|---------|-------|
| **OpenAI** | Async HTTP | 3x exponential | 30s | Query results |
| **Mapbox** | Async HTTP | 3x exponential | 10s | Geocoding results |
| **Lovdata** | Async HTTP | 2x linear | 15s | Search results |
| **BRREG** | Async HTTP | 3x exponential | 10s | Company data |
| **NVE** | Async HTTP | 2x linear | 10s | Flood data |
| **Jira** | Webhook + API | 3x exponential | 20s | None |
| **Resend** | Async HTTP | 3x exponential | 10s | None |

---

## Vedlegg: Diagram-notasjon

### Fargekoder

- 🔵 **Blå**: Backend-komponenter
- 🟣 **Lilla**: AI/Intelligence-komponenter
- 🟢 **Grønn**: Eksterne tjenester
- 🟡 **Gul**: Cache/Middleware
- 🔴 **Rød**: Sikkerhetskritiske komponenter
- ⚫ **Svart**: Frontend-komponenter

### Symboler

- **Rektangel**: Komponent/Container
- **Sylinder**: Database
- **Diamant**: Beslutningspunkt
- **Sirkel**: Start/Slutt
- **Pil**: Dataflyt/Avhengighet

---

**Dokumenteier:** Teknisk arkitekt  
**Sist oppdatert:** 12. februar 2026  
**Neste review:** 12. mai 2026
