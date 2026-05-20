# KI Kollega Fullverdig – full plan

Plan for implementering av Fullverdig modus: AI-first arkitektur med domeneagenter som utfører oppgaver (f.eks. internkontroll).

---

## 1. Visjon

**Fullverdig** skal være en AI-koordinator som:
- **Intensjon først** – tolker brukerens mål, ikke bare nøkkelord
- **Utfører oppgaver** – ikke bare svarer, men *gjør* ting (sjekker, oppretter, varsler)
- **Domeneagenter** – spesialiserte agenter per domene (internkontroll, kontrakter, eiendommer, etc.)
- **Proaktiv** – foreslår handlinger basert på kontekst

---

## 2. Arkitektur – oversikt

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BRUKER: "Sjekk internkontroll for Storgata 12"                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (AI-first)                                                      │
│ - Tolker intensjon                                                           │
│ - Velger domeneagent(er)                                                      │
│ - Koordinerer oppgaver                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┬───────────────┐
                    ▼               ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ INTERNKONTROLL│ │ KONTRAKTER   │ │ EIENDOMMER   │ │ ØKONOMI      │
│ AGENT         │ │ AGENT        │ │ AGENT        │ │ AGENT        │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │               │
                    ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ VERKTØY / API                                                               │
│ check_internal_control, create_case, get_property_cases, run_sql, ...       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Domeneagenter – detaljert

### 3.1 Internkontroll-agent

**Hensikt:** Utføre internkontroll-oppgaver på vegne av brukeren.

**Oppgaver agenten kan utføre:**

| Oppgave | Beskrivelse | Verktøy/API |
|---------|-------------|-------------|
| **Sjekk status** | Hent åpne interne kontrollsaker for eiendom | `check_internal_control_tool(property_id)` |
| **Liste avvik** | Vis alle avvik med prioritet og frist | `GET /internal-control/cases` |
| **Opprett saker** | Opprett initiale saker for eiendom | `POST /internal-control/cases/init?property_id=X` |
| **Vurder risiko** | Hvilke eiendommer har høyest internkontroll-risiko | SQL + `internal_control_cases` |
| **Påminn** | Eiendommer med forfallte saker | SQL |
| **Oppsummer** | Oppsummer internkontroll-status for region | SQL + Aggregering |

**Eksempel på brukerinteraksjon:**
- *Bruker:* "Sjekk internkontroll for Bufdir Helsfyr"
- *Agent:* Kjører `check_internal_control_tool`, returnerer resultat
- *Orchestrator:* Formulerer svar: "Bufdir Helsfyr har 2 åpne saker: 1 kritisk (brannrunde forfalt), 1 medium (sikkerhetsaudit). Vil du at jeg oppretter oppfølgingssak?"

**Utvidelser (fase 2):**
- **Opprett avvik** – Agent kan opprette ny InternalControlCase
- **Tildel bruker** – Agent kan tildele sak til ansatt
- **Send påminnelse** – Agent kan trigge Notification

---

### 3.2 Kontrakter-agent

**Oppgaver:**
- Liste kontrakter som utløper
- Oppsummer leietaker per eiendom
- Sammenlign kontraktsvilkår
- Varsle om manglende kontrakter

---

### 3.3 Eiendommer-agent

**Oppgaver:**
- Liste eiendommer med kriterier
- Sammenlign kostnad per kvm
- Risikovurdering (NVE, flom)
- Geografisk oversikt

---

### 3.4 Økonomi-agent

**Oppgaver:**
- Kostnadsanalyse per eiendom
- Avvik mellom budsjett og faktisk
- Regional oversikt

---

## 4. Implementeringsfaser

### Fase 1: Orchestrator + Internkontroll-agent (MVP)

**Mål:** Fullverdig kan svare på internkontroll-spørsmål og *utføre* sjekker.

| Steg | Beskrivelse | Estimat |
|------|-------------|---------|
| 1.1 | Ny backend: `POST /api/v1/ai/chat/fullverdig` – ekte implementasjon | 2 d |
| 1.2 | Orchestrator-node: LLM tolker intensjon → velger agent | 2 d |
| 1.3 | Internkontroll-agent: Wrapper rundt `check_internal_control_tool`, `get_property_cases` | 2 d |
| 1.4 | Integrasjon: Orchestrator → Internkontroll-agent → Writer | 1 d |
| 1.5 | Frontend: Fullverdig viser "Utfører oppgave..." under kjøring | 0.5 d |

**Leveranse:** Bruker kan si "Sjekk internkontroll for Storgata 12" og få faktisk resultat fra DB.

---

### Fase 2: Flere agenter + oppgavestyring

| Steg | Beskrivelse | Estimat |
|------|-------------|---------|
| 2.1 | Kontrakter-agent | 2 d |
| 2.2 | Eiendommer-agent | 2 d |
| 2.3 | Oppgavestyring: Agent kan foreslå "Vil du at jeg oppretter sak?" | 2 d |
| 2.4 | Bekreftelsesdialog: Bruker må bekrefte før skrivende operasjoner | 1 d |

---

### Fase 3: Proaktivt + skrivende operasjoner

| Steg | Beskrivelse | Estimat |
|------|-------------|---------|
| 3.1 | Proaktive varsler: "Du har 3 forfallte internkontroll-saker" | 2 d |
| 3.2 | Internkontroll-agent: Opprett case, tildel bruker | 2 d |
| 3.3 | Økonomi-agent | 2 d |
| 3.4 | Audit-log for agent-handlinger | 1 d |

---

## 5. Teknisk design – Fase 1

### 5.1 Ny graf: Fullverdig

```
                    ┌──────────────┐
                    │ ORCHESTRATOR │  ← LLM: "Hva vil brukeren? Hvilken agent?"
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  internkontroll     kontrakter        fallback
  _agent             _agent            (avansert)
         │                 │                 │
         └────────┬────────┘                 │
                  ▼                          │
         ┌──────────────┐                    │
         │   WRITER     │  ←─────────────────┘
         └──────────────┘
```

### 5.2 Orchestrator (intensjonstolkning)

```python
# Pseudokode
ORCHESTRATOR_PROMPT = """
Brukerens melding: {message}
Kontekst: {context}  # property_id, side, etc.

Velg ÉN agent:
- internkontroll: Spørsmål om avvik, sjekklister, internkontroll, HMS, brannvern, forfallte saker
- kontrakter: Spørsmål om kontrakter, utløp, leietakere
- eiendommer: Spørsmål om eiendommer, kostnad, areal, region
- analyst: Dataanalyse, statistikk, SQL (fallback til avansert)
- avansert: Alt annet – videresend til eksisterende LangGraph

Svar KUN med ett ord: internkontroll | kontrakter | eiendommer | analyst | avansert
"""
```

### 5.3 Internkontroll-agent

```python
# Fase 1: Read-only
async def internkontroll_agent(state: FullverdigState) -> dict:
    intent = state["orchestrator_choice"]
    if intent != "internkontroll":
        return {"next_step": "writer"}
    
    message = state["messages"][-1].content
    property_id = extract_property_id(message, state["context"])
    
    if property_id:
        result = await check_internal_control_tool(property_id)
    else:
        result = await get_all_internal_control_cases()
    
    return {
        "messages": [SystemMessage(content=f"INTERNKONTROLL_RESULTAT:\n{result}")],
        "next_step": "writer"
    }
```

### 5.4 API-endepunkt

```python
@router.post("/chat/fullverdig")
async def chat_fullverdig(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Fase 1: Kjør fullverdig-graf
    result = await fullverdig_service.chat(
        message=request.message,
        context=request.context,
        history=request.history,
        db=db
    )
    return ChatResponse(**result)
```

---

## 6. Filer som må opprettes/endres

| Fil | Endring |
|-----|---------|
| `backend/app/services/intelligence/fullverdig/` | Ny mappe |
| `backend/app/services/intelligence/fullverdig/__init__.py` | - |
| `backend/app/services/intelligence/fullverdig/service.py` | FullverdigService |
| `backend/app/services/intelligence/fullverdig/graph.py` | Orchestrator → Agent → Writer |
| `backend/app/services/intelligence/fullverdig/agents/internkontroll.py` | Internkontroll-agent |
| `backend/app/services/intelligence/fullverdig/state.py` | FullverdigState |
| `backend/app/api/v1/ai/chat.py` | Erstatt placeholder med fullverdig_service.chat() |
| `frontend/lib/domains/innsikt/kiKollegaService.ts` | chatFullverdig → POST /chat/fullverdig (streaming) |

---

## 7. Avhengigheter

- Eksisterende MCP-verktøy: `check_internal_control_tool`
- InternalControlService: `get_property_cases`, `create_initial_cases_for_property`
- API: `GET /internal-control/cases`, `POST /internal-control/cases/init`
- LangGraph (samme som Avansert)

---

## 8. Suksesskriterier

**Fase 1 ferdig når:**
1. Bruker velger Fullverdig og spør "Sjekk internkontroll for [eiendom]"
2. System returnerer faktiske åpne saker fra databasen
3. Svar er formulert på naturlig norsk (Writer)
4. Ingen regresjon på Enkel eller Avansert

---

## 9. Risiko og begrensninger

| Risiko | Mitigering |
|--------|------------|
| Skrivende operasjoner uten brukerbekreftelse | Fase 2: Alltid krev "Vil du at jeg gjør X?" før create/update |
| Agent velger feil domene | Orchestrator får tydelige eksempler; fallback til avansert |
| Ytelse (ekstra LLM-kall) | Orchestrator bruker gpt-4o-mini; caching av intent |
| Sikkerhet (RBAC) | Agenter bruker samme get_db/get_current_user som resten |

---

*Dokumentet er en plan for implementering. Ved oppstart skal Fase 1 prioriteres.*
