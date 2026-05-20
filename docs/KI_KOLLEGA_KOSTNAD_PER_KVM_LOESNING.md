# KI Kollega – Løsning for kostnad per kvadratmeter

**Dokumenttype:** Prosjektplan / Løsningsbeskrivelse  
**Versjon:** 1.0  
**Dato:** Februar 2025  
**Status:** Implementert

---

## 1. Sammendrag

KI Kollega er BEFS sin AI-assistent for eiendomsforvaltning. Løsningen beskriver en rettelse som sikrer at spørsmål om **kostnad per kvadratmeter** (vedlikehold per kvm) besvares korrekt i Avansert og Fullverdig modus. Tidligere returnerte systemet feil eller manglende data for slike spørsmål.

---

## 2. Bakgrunn og problemstilling

### 2.1 Kontekst

KI Kollega tilbyr tre moduser:

| Modus | Beskrivelse | Backend |
|-------|-------------|---------|
| **Enkel** | Én OpenAI-kall med alle domenedata i kontekst | `POST /api/v1/ai/chat/simple` |
| **Avansert** | LangGraph-flyt med verktøy (Researcher, Analyst, Writer) | `POST /api/v1/ai/chat` |
| **Fullverdig** | Orchestrator som delegerer til Avansert eller Internkontroll | `POST /api/v1/ai/chat/fullverdig` |

Kostnadsdata for eiendommer ligger i `properties.external_data.financials`:
- `total_manual_expenses` – manuelle vedlikeholdskostnader
- `total_spend_csv` – kostnader fra CSV-import
- **Totalkostnad vedlikehold** = summen av disse
- **Kostnad per kvm** = totalkostnad / `total_area` (når total_area > 0)

### 2.2 Problem

Brukere som spurte f.eks. *«Hva er de 5 eiendommer med høyest kostnad per kvadratmeter?»* i Avansert eller Fullverdig modus fikk:

- Svar om at systemet «ikke har spesifikke tall for kostnad per kvadratmeter»
- Eller feil/irrelevante data

**Årsak:** Analyst-noden ruter spørsmål som inneholder «kostnad» til ferdigskriptet `cost_analyzer_top`. Dette skriptet:
- Sorterer kun på **total kostnad** (rent + costs), ikke kostnad per kvm
- Bruker `manual_expenses`-array, som kan være tomt selv når `total_manual_expenses` og `total_spend_csv` er fylt

---

## 3. Løsning

### 3.1 Overordnet tilnærming

Spørsmål som handler om **kostnad per kvadratmeter** (kvm) rutes nå til **DSPy SQL Generator** i stedet for `cost_analyzer_top`. DSPy genererer dynamisk SQL basert på naturlig språk og schema, og kan beregne kostnad per kvm korrekt.

### 3.2 Ruteringslogikk i Analyst

```
Brukerens spørsmål
       │
       ▼
Inneholder "kostnad" ELLER "cost"?
       │
       ├── NEI ──► Fortsett med eksisterende logikk (audit, cost_analyzer_top for generell kostnad)
       │
       └── JA ──► Inneholder "kvm", "kvadratmeter", "kvadrat" eller "per kvm"?
                    │
                    ├── JA ──► Bruk DSPy (generer SQL for kostnad per kvm)
                    │
                    └── NEI ──► Bruk cost_analyzer_top (sorter på rent/costs/total)
```

### 3.3 SQL-eksempel i schema

For at DSPy skal generere riktig SQL, er følgende mønster lagt inn i `backend/app/config/SCHEMA.md`:

```sql
SELECT 
    name,
    address,
    total_area,
    (COALESCE((external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
     + COALESCE((external_data->'financials'->>'total_spend_csv')::numeric, 0)) AS total_cost,
    ROUND(((COALESCE(...) + COALESCE(...)) / NULLIF(total_area, 0))::numeric, 2) AS cost_per_sqm
FROM properties
WHERE total_area IS NOT NULL AND total_area > 0
ORDER BY cost_per_sqm DESC
LIMIT 10
```

---

## 4. Teknisk implementasjon

### 4.1 Endrede filer

| Fil | Endring |
|-----|---------|
| `backend/app/services/intelligence/agents/nodes/analyst.py` | Utvidet ruteringslogikk: nøkkelord «kvm», «kvadratmeter», «kvadrat», «per kvm» utelukker `cost_analyzer_top` og trigger DSPy |
| `backend/app/config/SCHEMA.md` | Lagt til SQL-eksempel for «eiendommer med høyest kostnad per kvadratmeter» |

### 4.2 Kodeendring (analyst.py)

**Før:**
```python
elif "cost" in content or "kostnad" in content:
    selected_script = "cost_analyzer_top"
    params = {"n": "5", "by": "total"}
```

**Etter:**
```python
elif ("cost" in content or "kostnad" in content) and not any(
    kw in content for kw in ["kvm", "kvadratmeter", "kvadrat", "per kvm"]
):
    # cost_analyzer_top sorterer kun på rent/costs/total – ikke kostnad per kvm.
    # Spørsmål om kostnad per kvadratmeter må bruke DSPy.
    selected_script = "cost_analyzer_top"
    params = {"n": "5", "by": "total"}
```

### 4.3 Flyt i systemet

1. Bruker sender spørsmål til KI Kollega (Avansert eller Fullverdig)
2. Supervisor ruter til **analyst** (pga. nøkkelord «kostnad», «kvm»)
3. Analyst: matcher «kostnad» + «kvm» → **ikke** cost_analyzer_top → fallback til DSPy
4. DSPy leser SCHEMA.md, genererer SQL for kostnad per kvm, kjører mot PostgreSQL
5. Resultat formateres som tabell og sendes til Writer
6. Writer formulerer kollegavennlig svar til brukeren

---

## 5. Datakilder og beregninger

### 5.1 Kostnadsfelt i databasen

| Felt | Type | Beskrivelse |
|------|------|-------------|
| `properties.total_area` | Float | Totalt areal i m² |
| `external_data.financials.total_manual_expenses` | Numeric | Manuelle vedlikeholdskostnader (NOK) |
| `external_data.financials.total_spend_csv` | Numeric | Kostnader fra CSV-import (NOK) |

### 5.2 Beregning

- **Totalkostnad vedlikehold** = `COALESCE(total_manual_expenses, 0) + COALESCE(total_spend_csv, 0)`
- **Kostnad per kvm** = totalkostnad / `NULLIF(total_area, 0)` (avrundet til 2 desimaler)

### 5.3 Enkel modus

Enkel modus (`/ai/chat/simple`) henter allerede en ferdigberegnet tabell «KOSTNAD PER EIENDOM» med kolonnene Eiendom, Areal, Totalkostnad og Kostnad per kvm. Denne løsningen påvirker kun Avansert og Fullverdig modus.

---

## 6. Testing og validering

### 6.1 Testspørsmål

Følgende spørsmål bør nå besvares korrekt:

- «Hva er de 5 eiendommer med høyest kostnad per kvadratmeter?»
- «Hvilke eiendommer har høyest kostnad per kvm?»
- «List eiendommer sortert på kostnad per kvadratmeter»
- «Hvilke eiendommer har lavest kostnad per kvm?»

### 6.2 Verifikasjon

1. Åpne KI Kollega i BEFS (Avansert eller Fullverdig modus)
2. Still ett av testspørsmålene over
3. Verifiser at svaret inneholder konkrete eiendomsnavn og kostnad per kvm (NOK/m²)
4. Sammenlign evt. med Enkel modus for å bekrefte at tallene stemmer

### 6.3 Fallback

Hvis DSPy feiler (f.eks. manglende data, schema-endring), returnerer Analyst en feilmelding til Writer, som formulerer et kollegavennlig svar om at data ikke kunne hentes.

---

## 7. Leveranser

| Leveranse | Status |
|-----------|--------|
| Ruteringslogikk i Analyst | ✅ Implementert |
| SQL-eksempel i SCHEMA.md | ✅ Implementert |
| Commit og deploy | ✅ Committet (push krever manuell kjøring) |

---

## 8. Vedlikehold og videre utvikling

### 8.1 Avhengigheter

- **DSPy SQL Generator** – må ha tilgang til oppdatert `SCHEMA.md`
- **PostgreSQL** – `properties` med `total_area` og `external_data.financials`
- **Query library** – ved gjentatte spørsmål kan DSPy lagre vellykkede SQL-mønstre for raskere kjøring

### 8.2 Mulige forbedringer

1. **cost_analyzer.py** – utvide `show_top` til å støtte `by="cost_per_sqm"` og bruke `total_manual_expenses` + `total_spend_csv` som fallback når `manual_expenses` er tom
2. **Parameterextraksjon** – forbedre uttrekking av «5» eller «10» fra brukerens spørsmål til LIMIT-parameter
3. **Query library** – manuelt seede med kostnad-per-kvm-spørringen for raskere første treff

### 8.3 Relaterte dokumenter

- `docs/KI_KOLLEGA_HOW_IT_WORKS.md` – fullstendig flytbeskrivelse
- `docs/KI_KOLLEGA_EKSEMPELSPORSMAL.md` – testspørsmål
- `docs/KI_KOLLEGA_TRE_MODUSER.md` – Enkel, Avansert, Fullverdig
- `backend/app/config/SCHEMA.md` – database-schema for Text-to-SQL

---

*Dokumentet er klart for bruk i prosjektplan, statusrapporter og kravspesifikasjoner.*
