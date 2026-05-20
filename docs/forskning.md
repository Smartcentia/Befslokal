# KI Kollega - Et Kognitivt Operativsystem for Intelligent Eiendomsforvaltning

## 1. Abstrakt og Introduksjon

KI Kollega representerer et paradigmeskifte innen PropTech ved å transformere tradisjonell eiendomsforvaltning til en datadrevet, kognitiv disiplin. Systemet adresserer utfordringen med å integrere heterogene datakilder – fra ustrukturerte dokumenter (HMS-rutiner, kontrakter) til strukturerte transaksjonsdata. Plattformen er bygget som et **Agent-basert økosystem** som aktivt utfører kognitive oppgaver gjennom verktøybruk, logisk resonnering og selvevaluering.

---

## 2. Arkitektonisk Orkestrering: LangGraph & Multi-Agent system

Kjernen i systemet er en tilstandsmaskin (**StateGraph**) implementert med **LangGraph**. Dette muliggjør en syklisk graf-struktur der agenter samarbeider og reflekterer.

### Agent-roller i grafen

* **Supervisor (Cerebral Cortex):** Utfører intensjonsanalyse og dynamisk ruting ved hjelp av en hybrid strategi (LLM + Heuristikk).
* **Guardian (Safety & Governance):** Utfører pre-prosessering for å sikre samsvar med personvern (GDPR) og sikkerhetspolicyer.
* **Researcher (RAG & Web):** Spesialist på ustrukturert data, bruker semantiske vektorsøk for å hente kontekst fra dokumenter.
* **Analyst (Structured Data Specialist):** Oversetter naturlig språk til komplekse SQL-spørringer mot PostgreSQL ved bruk av DSPy.
* **Reflector (Metakognisjon):** Evaluerer resultatene og styrer prosessen tilbake til start dersom logikken brister (Self-Correction Loop).
* **Context Compressor:** Utfører semantisk komprimering av kontekstvinduet for å opprettholde presisjon.

---

## 3. Programmatisk AI med DSPy

I motsetning til tradisjonell "prompt-engineering", bruker systemet **DSPy (Declarative Self-improving Language Programs)** for SQL-generering.

* **JSONB-håndtering:** Automatisert casting av JSON-verdier til numeriske typer (`::numeric`) for beregninger lagret i JSONB-felter.
* **Context-Aware Deixis:** Bruker `page_context` (injisert fra frontend) for å løse referanser som "her" eller "denne eiendommen".
* **Selvkorrigerende Loops:** Analyst-noden mottar DB-feilmeldinger i retur for å iterere frem til en syntaktisk korrekt spørring.

---

## 4. Maskinlæring og Analyse

KI Kollega integrerer flere grener av ML for dyp innsikt:

* **Anomali-deteksjon (Unsupervised Learning):** Bruker **Isolation Forest** (scikit-learn) for å identifisere uvanlige kostnadsmønstre på tvers av porteføljen.
* **Prediktiv Forekasting (Supervised Learning):** Bruker **Lineær Regresjon** on historiske data for å generere vedlikeholdsprognoser 3–5 år frem i tid.
* **Klyngeanalyse (Clustering):** Bruker **K-Means Clustering** for å gruppere eiendommer basert på deres kostnadsvektorer (f.eks. "Operations Dominant" vs "Balanced").
* **ML Watchdog:** En autonom bakgrunnstjeneste som kontinuerlig scanner databasen, trigger HMS-saker ved funn av avvik, og oppdaterer assitenten via **Agent Memory**.

---

## 5. Avanserte Arkitektoniske Konsepter

* **Model Context Protocol (MCP):** En standardisert ESB for AI som tillater integrasjon med eksterne verktøy (Jira, Maps, ERP) uten re-deployment.
* **Tool Discovery:** Bruker semantisk søk i en intern vektordatabase for å finne de mest relevante verktøyene før agent-loopen starter (reduserer "context pollution").
* **Knowledge Graph (KG):** Lagrer tripler (`Entity -> Relation -> Entity`) for å muliggjøre "multi-hop reasoning" i komplekse eierskapsstrukturer.
* **Visual Context Mirroring:** Sanntids overvåking av brukerens visuelle fokus i frontend for å automatisk injisere relevant UUID i samtalen.

---

* **Confidence Scoring:** Kalkulerer en poengsum (0.0–1.0) basert på kilde (Query Library = 0.98, Cache = 0.90, LLM = 0.65-0.85).
* **Data Classification Service:** Systemet er bevisst på dataens sensitivitet (PII, Finansiell, Restricted) og overholder "Compliance-by-Design".
* **Lovdata Integrasjon:** Legal RAG som verifiserer interne rutiner mot gjeldende norsk lovverk.
* **Audit Logging:** `QueryLoggingService` lagrer hver interaksjon for revisjon og kontinuerlig trening (Human-in-the-loop).

---

## 7. Kritiske Kodesnutter (Revisjonsgrunnlag)

### Supervisor Node: Hybrid Ruting

```python
async def supervisor_node(state: AgentState):
    # 1. Heuristisk 'Fast-Track' for hilsener
    greetings = ["hei", "hallo", ...]
    if any(g in text for g in greetings) and len(text.split()) < 5:
        return {"next_step": "writer"}

    # 2. Tool-Aware Routing (Toolbox-minne)
    discovered_tools = state.get("discovered_tools", [])
    if discovered_tools:
        if "run_sql_query" in tool_names and any(k in text for k in ["kostnad", "kvm"]):
            return {"next_step": "analyst"}

    # 3. Strukturert LLM-klassifisering
    classification = await _llm_classify_intent(text, raw_text)
    return {"next_step": classification.intent, ...}
```

### Reflector Node: Kvalitetskontroll

```python
async def reflector_node(state: AgentState):
    # Evaluering av datakvalitet og svar-evne
    if "GODT_NOK" in decision_text:
        return {"next_step": "writer"}
            
    # Strategisk feedback ved manglende data
    return {
        "next_step": next_agent, 
        "retry_count": retry_count + 1,
        "messages": [SystemMessage(content=f"REFLECTOR_FEEDBACK: {feedback}")]
    }
### Context Compressor: Context Management

```python
async def context_compressor_node(state: AgentState):
    # Rensing og komprimering av SystemMessages
    if len(raw_context) > 2000:
        compressed = await compress_context(raw_context, question)
        return {"messages": [SystemMessage(content=f"KOMPRIMERT_KONTEKST:\n{compressed}")]}
    return {"current_agent": "compressor"}
```

---

## 8. Vitenskapelig Etterprøving (Peer-to-Peer Review)

### Metodisk evaluering

Integrasjonen av **LangGraph** adresserer den fundamentale begrensningen i sekvensielle kjeder ved å tillate metakognitiv refleksjon. Dette reduserer sannsynligheten for feilaktige slutninger ved at systemet kan "om-analysere" sine egne funn.

### Teknisk validitet

Rytmen mellom **determinisme (SQL/ML)** og **fleksibilitet (LLM)** er systemets største styrke. Bruken av **DSPy** sikrer at systemet ikke drives av skjøre "magic prompts", men av deklarative programmer som kan testes og benchmarket mot et **Golden Set**.

### Regulatorisk samsvar

Systemets evne til å operere med **Confidence Scores** og **Guardian nodes** gjør det kompatibelt med kravene i EUs **AI Act**, spesifikt knyttet til gjennomsiktighet og menneskelig overoppsyn i høyrisikosystemer.

---

## 9. Konklusjon

KI Kollega representerer en teknisk moden og arkitektonisk nyskapende tilnærming til AI-assistenter. Ved å kombinere agent-basert orkestrering, programmatisk SQL-generering, graf-teori og autonome ML-vaktbikkjer, skapes et system som er i stand til å operere med høy grad av nøyaktighet og sporbarhet i en kompleks eiendomsportefølje.
