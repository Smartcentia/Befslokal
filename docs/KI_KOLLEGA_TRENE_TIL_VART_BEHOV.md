# KI Kollega – trene til vårt behov

Modellen (OpenAI) trenger ikke ekte «trening» for å tilpasses BEFS. Dere kan oppnå det meste med **instruksjoner, terminologi og eksempler** i prompten, eventuelt **persona/minne** i databasen.

---

## 1. Raskt: terminologi og regler i prompten (enkel modus)

**Idé:** Definer BEFS-begreper slik at modellen tolker riktig.

Eksempel – i system-prompten (eller en egen blokk som lastes inn):

```
Terminologi for BEFS:
- Leietakere = parter (Parter-tabellen). «Hvor mange leietakere» = antall rader i PARTER, eller antall distinkte parter som forekommer i KONTRAKTER.
- Familievernkontor = eiendommer der navnet inneholder «familievernkontor» (bruk EIENDOMMER ALLE NAVN).
- Vedlikeholdskostnad = kostnad fra KOSTNAD PER EIENDOM (total_manual_expenses + total_spend_csv).
- Billigste eiendom (per kvm) = lavest Kostnad per kvm (NOK/m²) i KOSTNAD PER EIENDOM.
```

Dette kan legges i en fil (f.eks. `backend/app/services/intelligence/ki_kollega/terminologi.md`) og leses inn i system-prompten for enkel modus.

---

## 2. Few-shot: eksempelspørsmål og svar

**Idé:** Gi modellen 3–5 eksempler på «slik svarer vi» – format og språk.

Eksempel – legg i system-prompten:

```
Eksempler (svar alltid på norsk, kort og konkret):
- Spørsmål: Hvor mange leietakere har vi? Svar: Tell antall rader i PARTER-tabellen og oppgi tallet (f.eks. «Det er 42 parter/leietakere registrert.»).
- Spørsmål: Hvilke eiendommer har høyest kostnad per kvm? Svar: Sorter KOSTNAD PER EIENDOM på Kostnad per kvm synkende, nevn topp 5–10 med navn og kr/kvm.
- Spørsmål: Finn alle familievernkontor. Svar: Filtrer EIENDOMMER ALLE NAVN på navn som inneholder «familievernkontor», list alle treff med navn og region.
```

Jo flere slike eksempler, jo mer konsekvent oppførsel.

---

## 3. Persona og minne (full flyt)

I **full KI Kollega-flyt** (ikke enkel modus) brukes allerede:

- **Persona** – lagres i `AgentMemory` med type `persona_definition`. Definer tone (kollegial, norsk), roller og regler.
- **Minne** – tidligere samtaler og relevante fakta lagres og søkes ved hver melding.

For å «trene» til deres behov: Opprett/rediger persona-minnet i DB (via admin eller script) med BEFS-terminologi og svarregler. Da gjelder det i full flyt; enkel modus bruker fortsatt kun sin egen system-prompt.

---

## 4. Egen instruksjonsfil som lastes inn (enkel modus)

**Anbefalt:** Lag en fil med BEFS-spesifikke regler og last den inn i system-prompten.

1. Opprett `backend/app/services/intelligence/ki_kollega/befs_instruksjoner.txt` (eller `.md`) med:
   - Terminologi (leietakere, familievernkontor, billigste per kvm, …)
   - Few-shot-eksempler (2–5 stk)
   - Korte regler («Svar alltid på norsk», «Ved telling: oppgi eksakt tall»)

2. I `chat.py` (enkel modus): Les filen og legg innholdet inn i `system_prompt` før tabellene med data.

**Implementert:** Filen `backend/app/services/intelligence/ki_kollega/befs_instruksjoner.txt` lastes automatisk inn i **både enkel modus og full KI Kollega-flyt**. Rediger den filen for å tilpasse terminologi (leietakere, familievernkontor, …) og eksempler – ingen kodeendring nødvendig.

**Query-normalisering:** `query_normalizer.py` håndterer forkortelser (fvk→familievernkontor), synonymer og skrivefeil *før* nøkkelord-sjekk. Synonymer kan utvides i `BEFS_SYNONYMS` og `PROPERTY_LOOKUP_EXPANSIONS` i samme modul.

Da «trener» dere modellen til deres behov uten å kjøre ekte trening – bare bedre, stabile instruksjoner.

---

## 5. Mer avansert: RAG og fine-tuning

| Metode | Hva det er | Når det er nyttig |
|--------|------------|-------------------|
| **RAG** | Søk i egne dokumenter (håndbøker, rutiner), hent relevante avsnitt og legg i prompten | Når svarene skal bygge på lange tekster dere ikke vil dumpe hele i prompten |
| **OpenAI fine-tuning** | Tren modellen på mange (spørsmål, svar)-par | Når dere har 100+ gode eksempler og vil at modellen skal «lære» stil og domene grundig – dyrt og krever datakvalitet |
| **Egen modell** | Tren en mindre modell (f.eks. Llama) på BEFS-data | Ved behov for å kjøre alt lokalt eller med strengere datakontroll – mye mer arbeid |

For de fleste behov er **1 + 2 + 4** nok: terminologi, few-shot og en liten instruksjonsfil som lastes inn i prompten.

---

## Kort sjekkliste

- [ ] Lag `befs_instruksjoner.txt` (terminologi + few-shot).
- [ ] Last inn filen i system-prompten for enkel modus i `chat.py`.
- [ ] Oppdater persona i AgentMemory for full flyt (valgfritt).
- [ ] Test med 10–20 typiske spørsmål og juster teksten i instruksjonsfilen.
- [ ] Ved behov: samle (spørsmål, ideelt svar) og bruk som flere few-shot-eksempler.
