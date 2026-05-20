# KI Kollega - Dokumentasjons- og Arkitekturoversikt

## 1. Systemoversikt og Formål

**KI Kollega** er hjernen i BEFS-plattformen – et avansert multi-agent system designet for å automatisere kompleks eiendomsforvaltning, finansiell analyse og regulatorisk etterlevelse. Systemet fungerer ikke som en enkel chatbot, men som et **agentisk økosystem** som kan resonnare, planlegge, og utføre verktøy-baserte handlinger mot sanntidsdata.

### Hovedmål

* **Datademokratisering:** Gjør komplekse SQL-data tilgjengelig via naturlig språk.
* **Proaktiv Overvåking:** Oppdager avvik og muligheter før de blir kritiske feil.
* **Regulativ Presisjon:** Sikrer at HMS- og kontraktshåndtering følger norske lover og interne rutiner.

---

## 2. Arkitekturen: LangGraph og Agentisk Orkestrering

Systemet er bygget på **LangGraph**, som muliggjør en syklisk graf-basert flyt. Dette skiller seg fra tradisjonelle lineære "chains" ved at agenter kan gå tilbake, be om avklaringer, eller selv-korrigere basert på feedback.

### Sentrale Grafer og Flyter

* **StateGraph:** Definerer den globale tilstanden (`AgentState`) som flyter mellom noder.
* **Cyclic Control:** Tillater "reflection loops" hvor en agent kan be om en ny kjøring dersom dataene er mangelfulle.

---

## 3. Agent-Roller (The Core Team)

### A. Supervisor (Dirigenten)

* **Ansvar:** Intensjonsanalyse og ruting.
* **Teknologi:** Bruker `gpt-4o-mini` med strukturert output (`PydanticOutputParser`).
* **Logikk:** Benytter en hybrid tilnærming:
    1. *Fast-track:* Kjenner igjen enkle hilsener via regex/heuristikk.
    2. *Semantic Classification:* Klassifiserer brukerens forespørsel i kategorier som `ANALYTICS`, `RESEARCH`, `GOVERNANCE`, eller `MAINTENANCE`.

### B. Guardian (Sikkerhetsvakten)

* **Ansvar:** Pre-prosessering for sikkerhet.
* **Oppgaver:** PII-maskering (Personally Identifiable Information), sjekk mot slettningsregler, og sikring av at sensitive finansielle data kun aksesserer lovlige ruter.

### C. Analyst (Data-Spesialisten)

* **Ansvar:** Strukturert datauthenting og oppgavehåndtering.
* **Teknologi:** **DSPy (Programmatic Prompting)** for generering av robuste SQL-spørringer.
* **Spesialitet:** Automatisk håndtering av PostgreSQL JSONB-felter, casting til numeriske typer ved beregninger, og selv-korrigering ved SQL-syntaksfeil.
* **Jira-integrasjon:** Kan opprette og spore oppgaver direkte i Jira basert på analyser (f.eks. "Opprett en sak på å sjekke strømforbruket på Storgata").

### D. Researcher (Dokument-Eksperten)

* **Ansvar:** Ustrukturert data (PDF, rutiner, kontrakter).
* **Metode:** **RAG (Retrieval-Augmented Generation)** kombinert med semantisk søk i en vektordatabase (pgvector).
* **Kilder:** Lovdata-integrasjon, interne HMS-manualer, og leiekontrakter.

### E. Reflector (Kritikeren)

* **Ansvar:** Kvalitetssikring før svar sendes brukeren.
* **Logikk:** Sammenligner hentet data med det opprinnelige spørsmålet. Dersom dataene er "halvveis", instruerer den systemet til å utføre nye søk med spesifikk feedback.

### F. Context Compressor

* **Ansvar:** Token-effektivitet og hukommelse.
* **Metode:** Når samtalen passerer en gitt terskel (f.eks. 2000 tokens), utføres en semantisk komprimering som beholder kritiske entiteter (UUID-er, beløp, datoer) mens flertydig småprat fjernes.

---

## 4. Den Maskinlærende Motoren (AI Services)

KI Kollega støttes av dedikerte ML-tjenester lokalisert i `backend/app/services/analytics/`:

* **Anomali-deteksjon:** Benytter **Isolation Forest** for å identifisere "ghost expenses" eller uvanlige trender i energiforbruk og vedlikehold.
* **Prediksjon:** **Lineær Regresjon** og tidsseriemodeller for å beregne fremtidige vedlikeholdskostnader og leieinntektsutvikling.
* **Clustering:** Grupperer eiendommer basert på ytelsesprofiler for å finne underpresterende enheter i porteføljen.
* **ML Watchdog:** En autonom prosess som kjører i bakgrunnen, trigger agent-systemet hvis data-metrics bryter gitte terskelverdier (f.eks. en 20% økning i driftskostnader på ett kvartal).

---

## 5. Teknisk Stack og Integrasjoner

* **Språkmodeller:** GPT-4o (hovedresonnering), GPT-4o-mini (ruting og summarisering).
* **Database:** PostgreSQL med **pgvector** for Agent Memory (langtidshukommelse).
* **Orkestrering:** LangGraph (Python).
* **SQL-logikk:** DSPy for deklarativ spørrings-optimalisering.
* **Frontend-kobling:** Real-time websockets med visual context mirroring (AI-en ser det du ser på skjermen).

---

## 6. Tillit og Gjennomsiktighet (Transparency)

Systemet beregner en **Confidence Score** for alle svar:

1. **Høy (0.95+):** Data hentet direkte fra SQL via verifiserte biblioteker.
2. **Middels (0.75-0.90):** Kombinasjon av dokument-søkt og LLM-slutning.
3. **Lav (<0.70):** Rent generativt svar med forbehold om "hallusinering".

---

* **Routing Accuracy:** 100% suksessrate på "30/30 baseline test" for krysning mellom analyse og generelle spørsmål.
* **Self-Correction:** Analyst-noden retter nå 90% av egne SQL-feil i første iterasjon ved bruk av database-feedback.
* **Memory Depth:** Systemet husker tidligere eiendoms-valg på tvers av sesjoner ved hjelp av `SessionState` og vektorminne.

---

*Denne dokumentasjonen reflekterer KI Kollega versjon 2.0 (Februar 2026).*
