# KI Kollega: Det Definitive Referansedokumentet (v2.0)

Dette dokumentet utgjør den komplette tekniske og funksjonelle beskrivelsen av **KI Kollega**-systemet i BEFS-plattformen. Det dekker arkitektur, agent-logikk, maskinlæring, sikkerhet og implementeringsdetaljer.

---

## 1. Oversikt og Systemfilosofi

**KI Kollega** er ikke en tradisjonell chatbot, men et **Agentisk Operativsystem**. Det er bygget for å transformere rå eiendomsdata til handlingsbar innsikt gjennom:

* **Autonomi:** Evnen til å velge verktøy og utføre analyser uten steg-for-steg instruksjoner.
* **Refleksjon:** Systemet evaluerer sine egne svar og korrigerer feil før brukeren ser dem.
* **Hybrid Intelligens:** Kombinerer store språkmodeller (LLMs) med deterministiske SQL-skript og statistiske ML-modeller.

---

## 2. Teknisk Arkitektur: LangGraph Orkestrering

Systemet er implementert som en syklisk graf ved bruk av **LangGraph** (plassert i `backend/app/services/intelligence/agents/graph.py`).

### Grafens Topologi (Noder og Flyt)

1. **Supervisor (`supervisor.py`):** Inngangspunktet. Utfører intensjonsanalyse og ruter til riktig spesialist.
2. **Guardian (`guardian.py`):** Sikkerhetsfilter. Maskerer PII (personopplysninger) og validerer forespørsler.
3. **Researcher (`researcher.py`):** Spesialist på ustrukturert data (RAG). Søker i PDF-er, HMS-manualer og Lovdata.
4. **Analyst (`analyst.py`):** Spesialist på strukturerte data. Kjører SQL og ML-skript.
5. **Memory (`memory.py`):** Henter historisk kontekst og faste brukerpreferanser fra `pgvector`.
6. **Reflector (`reflector.py`):** Kvalitetskontroll. Kan sende logikken i "loop" hvis svaret er ufullstendig.
7. **Compressor (`context_compressor.py`):** Styrer token-forbruk ved å summarisere metadata.
8. **Writer (`writer.py`):** Formaterer det endelige svaret til brukeren (Markdown/Tabeller).

---

## 3. Spesialist-Agentene i Detalj

### A. Supervisor (Kognitiv Ruting)

Bruker en **Hybrid Classifier**:

* **Deterministisk:** Sjekker etter nøkkelord for hurtigruting (f.eks. "Hei" -> Writer).
* **LLM-basert:** Klassifiserer komplekse spørsmål i domener (`ANALYTICS`, `RESEARCH`, `PORTFOLIO`).
* **Fil:** `backend/app/services/intelligence/agents/nodes/supervisor.py`

### B. Analyst (Data & ML)

Analyst-noden opererer i tre moduser:

1. **Script Mode:** Kjører pre-definerte, sikre analyse-skript (f.eks. `cost_analyzer_top`, `audit_contracts`).
2. **DSPy Mode:** Bruker deklarativ AI for å generere ad-hoc SQL for komplekse spørsmål som involverer firmaer, leietakere eller avviksberegninger.
3. **Task Mode (Jira):** Kan opprette, tildele og spore oppgaver i Jira direkte fra analyseresultater.
4. **Fil:** `backend/app/services/intelligence/agents/nodes/analyst.py`

### C. Researcher (Ustrukturert RAG)

* Integrerer med **pgvector** for semantisk søk.
* **Hybrid Search:** Kombinerer BM25 (tekstlikhet) med Vector Embeddings for maksimal presisjon i HMS-dokumentasjon.
* **Fil:** `backend/app/services/intelligence/agents/nodes/researcher.py`

---

## 4. Maskinlæring og Analytiske Tjenester

KI Kollega har tilgang til en robust "verktøykasse" av ML-modeller lokalisert i `backend/app/services/analytics/`:

| Modell / Skript | Metode | Formål |
| :--- | :--- | :--- |
| `ml_financial_anomalies` | **Isolation Forest** | Finn uforklarlige kostnadshopp eller "ghost expenses". |
| `ml_financial_forecasting` | **Lineær Regresjon** | Prognose for vedlikeholdsbehov neste 1-5 år. |
| `ml_financial_patterns` | **K-Means Clustering** | Gruppere eiendommer etter driftsrisiko og energiprofil. |
| `audit_contracts` | Heuristisk + LLM | Identifisere utløpende kontrakter og manglende KPI-er. |

---

## 5. Sikkerhet og Tillit (Guardian & Reflector)

Sikkerhet er innebygd i selve grafen:

* **PII Masking:** Automatisk fjerning av personnavn og telefonnumre fra kontekstvinduet.
* **SQL Injection Protection:** Alle ad-hoc spørringer generert av DSPy kjøres i en skrivebeskyttet transaksjon med begrensede rettigheter.
* **Confidence Scoring:** Hvert svar inneholder en intern "tillitsskår". Ved lav skår tvinger **Reflector**-noden systemet til å angi usikkerhet til brukeren.

---

## 6. Programmatisk AI med DSPy

Vi bruker **DSPy** i stedet for tradisjonell prompt engineering for å sikre:

* **Type-sikkerhet:** Automatisk casting av PostgreSQL-data (f.eks. `::numeric` for JSONB-felter).
* **Konsistens:** Samme spørsmål gir samme logiske struktur hver gang.
* **Self-Correction:** Hvis en SQL-spørring feiler, bruker DSPy feilmeldingen til å automatisk omskrive spørringen i neste iterasjon.

---

## 7. Katalogstruktur for KI Kollega

```text
backend/app/services/intelligence/
├── agents/
│   ├── graph.py            # Definisjon av StateGraph og noder
│   ├── state.py            # Definisjon av AgentState (Pydantic)
│   ├── nodes/              # Implementasjon av hver agent
│   │   ├── supervisor.py
│   │   ├── analyst.py
│   │   ├── researcher.py
│   │   ├── reflector.py
│   │   └── compressor.py
│   └── utils.py            # Logge- og sporingsverktøy
└── ki_kollega/
    └── service.py          # API-grensesnitt mot frontend
```

---

## 8. Konklusjon for Revisjon og Forskning

KI Kollega representerer "state-of-the-art" innen anvendt AI for eiendomsforvaltning. Ved å flytte seg fra en reaktiv chatbot til et proaktivt multi-agent system, oppnår man:

1. **Mindre hallusinering** (via Reflector & deterministisk SQL).
2. **Høyere sikkerhet** (via Guardian & PII masking).
3. **Dypere innsikt** (via integrert ML-analyse).

*Dette dokumentet er generert som en uttømmende teknisk referanse for BEFS-teamet og tilknyttet forskningsarbeid.*
