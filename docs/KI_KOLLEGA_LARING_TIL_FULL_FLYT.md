# Læring fra enkel modus – ta med til full KI Kollega

Dette dokumentet oppsummerer **hva vi lærte** i enkel modus og **konkrete forbedringer** for den mer avanserte KI Kollega (LangGraph-flyt).

---

## 1. Hva vi lærte (enkel modus)

| Læring | Hva vi gjorde i enkel modus |
|--------|-----------------------------|
| **Spørsmålstype → datakilde** | Eksplisitt mapping i prompt: «Alle X» → EIENDOMMER ALLE NAVN, «kostnad per kvm» → KOSTNAD PER EIENDOM, «leietakere» → PARTER, osv. Modellen trenger å vite *hvilken* tabell som gjelder. |
| **Terminologi** | BEFS-begreper definert: leietakere = parter, billigste per kvm = lavest Kostnad per kvm, familievernkontor = navn inneholder «familievernkontor». Uten dette tolket modellen feil. |
| **«Alle X» krever full liste** | For «alle familievernkontor» må vi ha eiendomsnavn sortert på *navn* (ikke bare de største etter areal), og instruere: list *alle* treff, ikke bare de første. |
| **Synonymer for brukeruttrykk** | «Billigste eiendom basert på kvm og pris» = lavest kostnad per kvm. «Pris per kvm» i BEFS-kontekst = vedlikeholdskostnad per kvm. Disse må stå i prompten. |
| **Instruksjonsfil uten kodeendring** | `befs_instruksjoner.txt` med terminologi + few-shot lastes inn i prompten. Endring av oppførsel uten å deploye ny kode. |
| **Alle data, ingen LIMIT** | For å «lese alle data» fjernet vi LIMIT i spørringene – full portefølje (f.eks. 199 eiendommer) med i konteksten. |
| **Kostnadsdata må være med** | Spørsmål om «høyest kostnad per kvm» krever en egen datakilde (KOSTNAD PER EIENDOM fra external_data.financials). Uten det svarer modellen at den ikke har data. |

---

## 2. Konkrete forbedringer for full KI Kollega

### 2.1 Persona + BEFS-instruksjoner (service.py / AgentMemory)

**Læring:** Samme terminologi og regler som i enkel modus bør gjelde i full flyt.

**Tiltak (implementert):** I `ki_kollega/service.py` lastes `get_befs_instruksjoner()` (filen `ki_kollega/befs_instruksjoner.txt`) og **legges alltid til** i persona før grafen kalles. Persona fra AgentMemory (hvis satt) brukes som base, deretter BEFS-instruksjonene. Da får full flyt samme terminologi og regler som enkel modus.

### 2.2 Writer – samme regler som enkel modus (writer.py)

**Læring:** Writer bør bruke samme språkregler og tolking (leietakere = parter, billigste = lavest kostnad per kvm).

**Tiltak:** I writer-nodens system prompt: inkluder en kort BEFS-blokk (terminologi + «ved telling oppgi eksakt tall», «ved «alle X» list alle treff»). Enten hardkodet eller hentet fra samme `befs_instruksjoner.txt`.

### 2.3 Supervisor – ruting for «alle X» og kostnad (supervisor.py)

**Læring:** «Alle familievernkontor», «hvor mange leietakere», «kostnad per kvm» må rutes til noder som har tilgang til riktig data (researcher med navnesøk, analyst med SQL).

**Tiltak:**
- Legg til nøkkelord: `"alle "`, `"familievernkontor"`, `"leietakere"`, `"hvor mange parter"`, `"kostnad per kvm"`, `"billigste per kvm"`.
- «Alle X» (navnesøk på eiendommer) → researcher (lookup_properties eller eget verktøy som søker på navn og returnerer alle treff).
- «Hvor mange leietakere/parter» og «kostnad per kvm» → analyst (SQL som teller parter eller henter kostnad per eiendom).

### 2.4 Analyst / SQL – schema og faste spørringer

**Læring:** Kostnad per kvm kommer fra `properties.external_data.financials` (total_manual_expenses + total_spend_csv). Analyst må kunne generere eller kjøre spørringer som bruker disse feltene.

**Tiltak:**
- I `config/SCHEMA.md` (eller tilsvarende som Analyst/DSPy bruker): beskriv at «vedlikeholdskostnad» / «kostnad per eiendom» kan beregnes fra `properties.external_data->'financials'->>'total_manual_expenses'` og `'total_spend_csv'`, og at `total_area` finnes på `properties`.
- Vurder et **SAFE_ANALYSIS_SCRIPT** for «kostnad per kvm» (eiendommer med total_area og total_cost, sortert på cost/total_area) slik at analyst ikke trenger å generere kompleks JSONB-SQL hver gang.

### 2.5 Researcher – «alle X» returnerer alle treff

**Læring:** lookup_properties (navn/adresse) bør ved «alle X» returnere *alle* treff, ikke en kort liste. I enkel modus brukte vi en egen liste «EIENDOMMER ALLE NAVN» uten LIMIT.

**Tiltak:** I `_tool_lookup_properties` eller tilsvarende: hvis brukerens spørsmål inneholder «alle» + et navn/søkeord, øk grensen eller fjern LIMIT slik at alle matchende eiendommer returneres til writer.

### 2.6 Én kilde til sannhet for BEFS-regler

**Læring:** Unngå at enkel modus og full flyt får ulike regler.

**Tiltak:** Bruk **én fil** (`befs_instruksjoner.txt`) både i enkel modus og i full flyt (persona eller writer). Da oppdaterer dere kun ett sted når terminologi eller regler endres.

---

## 3. Sjekkliste for å ta læringen videre

- [ ] **Persona / service.py:** Last inn `befs_instruksjoner.txt` i tillegg til (eller som del av) persona før `app.ainvoke(inputs)`.
- [ ] **Writer:** Legg BEFS-terminologi og regler (kort versjon eller referanse til samme fil) i writer-nodens system prompt.
- [ ] **Supervisor:** Utvid nøkkelord for «alle X», «leietakere», «kostnad per kvm» og ruter til analyst/researcher der det passer.
- [ ] **Analyst/SCHEMA:** Dokumenter external_data.financials og evt. faste skript for kostnad per kvm.
- [ ] **Researcher/lookup:** Sørg for at «alle X»-søk returnerer alle treff (ingen unødvendig LIMIT).
- [ ] **Test:** Kjør de samme 10–20 spørsmålene i full flyt som i enkel modus (leietakere, familievernkontor, kostnad per kvm, billigste per kvm) og juster ruting/persona til svarene blir like gode.

---

## 4. Kort oppsummering

| Fra enkel modus | Til full KI Kollega |
|-----------------|---------------------|
| Spørsmålstype → tabell | Persona + writer får samme mapping; supervisor ruter «kostnad/alle/leietakere» til riktig node |
| BEFS-terminologi | Persona eller befs_instruksjoner.txt lastes inn i full flyt |
| «Alle X» = full liste | Researcher/lookup returnerer alle treff; analyst får evt. SQL uten LIMIT der det er riktig |
| Kostnad per kvm | Analyst + schema + evt. faste skript for external_data.financials |
| Én instruksjonsfil | Bruk befs_instruksjoner.txt både i enkel modus og i full flyt |

Da tar dere med læringen fra enkel modus inn i den mer avanserte KI Kollega uten å bygge alt på nytt.
