# KI Kollega – tre moduser

Brukeren kan velge mellom tre typer KI Kollega. Dette gir tydelig produktlag og mulighet til å utvikle «fullverdig» over tid uten å bryte det som fungerer i dag.

---

## 1. KI Kollega Enkel

**Hva:** Én OpenAI-kall med alle domenedata (eiendommer, kontrakter, parter, enheter, sentre, kostnad per eiendom) i system-prompten. Ingen agent-graf, ingen verktøy.

**Når:** Raskt, forutsigbart svar. God når full flyt feiler eller når du vil ha enkel, transparent oppførsel.

**Backend:** `POST /api/v1/ai/chat/simple`  
**Frontend:** Valg «Enkel».

---

## 2. KI Kollega Avansert (dagens full flyt)

**Hva:** LangGraph-flyt: Supervisor → Guardian → Researcher → Analyst → Writer. Verktøy (lookup_properties, run_sql_query, search_documents, Lovdata), BEFS-instruksjoner i persona, minne fra AgentMemory.

**Når:** Når du vil ha dokumenter, Lovdata, SQL-analyse og mer fleksibel ruting – men fortsatt regelstyrt.

**Backend:** `POST /api/v1/ai/chat`  
**Frontend:** Valg «Avansert».

---

## 3. KI Kollega Fullverdig (ekte AI-first)

**Hva:** (Under utvikling.) Intensjon først, AI som koordinator med verktøy, RAG på deres dokumenter, støtte for åpne spørsmål og oppfølgingsforslag. Mindre hardkodede regler, mer «tenk selv».

**Når:** Når løsningen er klar – for åpne spørsmål, anbefalinger, proaktive innspill og mer naturlig dialog.

**Backend:** `POST /api/v1/ai/chat/fullverdig` (placeholder i dag – kan videresende til avansert eller vise «under utvikling»).  
**Frontend:** Valg «Fullverdig».

---

## Valg i UI

- **Enkel:** Checkbox «Enkel modus» erstattes med en **modusvelger**: tre alternativer (Enkel | Avansert | Fullverdig).
- Valg lagres i `localStorage` (f.eks. `ki_kollega_mode`).
- Ved Fullverdig (fase 1): vis kort info om at det er under utvikling og anbefal Avansert inntil videre, eller kall samme backend som Avansert med et flagg.

---

## Fordeler med tre moduser

- Brukeren ser tydelig at det finnes ulike nivåer og kan velge etter behov.
- Enkel og Avansert forblir stabile; Fullverdig kan bygges ut uten å røre dem.
- Dere kan A/B-teste eller rulle ut Fullverdig gradvis.
