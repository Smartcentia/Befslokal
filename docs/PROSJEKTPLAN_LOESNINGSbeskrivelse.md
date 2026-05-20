# Løsningsbeskrivelse – BEFS / KNOWME

**Dokumenttype:** Prosjektplan – løsningsbeskrivelse  
**Versjon:** 1.0  
**Sist oppdatert:** Februar 2025

---

## 1. Hensikt og mål

**BEFS** (Bufetat Eiendomsforvaltningssystem), også kjent som **KNOWME**, er et digitalt eiendomsforvaltningssystem utviklet for Bufetat. Løsningen samler eiendomsforvaltning, kontrakter, økonomi og HMS (helse, miljø og sikkerhet) i én plattform, med en KI-assistent (KI-Kollega) som støtter brukere med naturlig språk.

**Hovedmål:**
- Samle og strukturere eiendoms-, kontrakts- og økonomidata på ett sted
- Støtte beslutninger med risikovurdering, kostnadsanalyse og budsjett
- Automatisere internkontroll og HMS-oppfølging
- Gjøre informasjon tilgjengelig via KI-assistent som svarer på naturlig språk

---

## 2. Løsningsarkitektur

### 2.1 Teknologisk stack

| Komponent | Teknologi | Hosting |
|-----------|-----------|---------|
| **Frontend** | Next.js (App Router), TypeScript, Tailwind CSS | Vercel |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic | Railway |
| **Database** | PostgreSQL (serverless) | Supabase |
| **Autentisering** | NextAuth (Credentials + Google), JWT | — |
| **Kart** | Mapbox | — |

### 2.2 Systemgrenser og integrasjoner

Løsningen integrerer med:
- **NVE** (Norges vassdrags- og energidirektorat) – hydrologiske stasjoner og flomvarsel
- **Kartverket** – geokoding og fylkesnummer
- **Brønnøysundregistrene (Brønnøysund)** – bedriftsinformasjon
- **Lovdata** – lover og forskrifter
- **Bufdir.no** – eiendomsliste og bilder (pipeline)
- **OpenAI** – KI-Kollega (LLM, embeddings, SQL-generering)

---

## 3. Funksjonelle moduler

### 3.1 Eiendommer og kontrakter

- **Eiendomsregister:** Oversikt over alle lokasjoner med kartvisning
- **Enheter:** Leiligheter, lokaler og areal per eiendom
- **Kontrakter:** Digitale kopier av leieavtaler, koblet mot eiendommer
- **Utløpsvarsler:** Automatisk varsling ved kontrakter som løper ut
- **Parter:** Leietakere, eiere og leverandører med BRREG-oppslag og Due Diligence

### 3.2 Økonomi og analyse

- **Kostnadsoversikt:** Kategorisering av utgifter (eiendom, drift, investering)
- **Kostnadsanalyse:** Sammenligning av utgifter mot årlig husleie (ratioer, vurderingsgrenser)
- **Budsjett:** Syntetisk budsjettgenerering fra historiske kostnader eller forbruk
- **Variansanalyse:** Budsjett vs. faktisk per kategori, måned og kvartal
- **Avvik:** Varsling ved avvik mellom faktura, budsjett og kontrakt

### 3.3 Risikovurdering

- **Risikoscore (0–100):** Proxy-indikatorer for sannsynlighet og konsekvens
- **Ekstern risiko:** Bygningsalder, areal, nærhet til vannvei (NVE), flomvarsel
- **Operasjonell risiko:** Åpne avvik i internkontroll
- **Prioriteringsindeks:** Rangering av eiendommer etter oppfølgingsbehov
- **Risikobildet:** Oversikt over eiendommer sortert etter prioriteringsindeks

### 3.4 HMS og internkontroll

- **Internkontroll-saker:** Strukturert oppfølging med status og frister
- **Sjekklister:** System- og brukerdefinerte maler (f.eks. brannslukker, rømningsveier)
- **Årshjul:** Oppgaver i kalender basert på byggtype
- **Aktivitetshub:** Tilgjengelige aktivitetsmaler for eiendommer
- **Cron-jobs:** Automatisk prosessering av forfalte og pågående saker

### 3.5 KI-Kollega (AI-assistent)

- **Naturlig språk:** Brukere stiller spørsmål på vanlig norsk
- **Kontekstbevisst:** Forstår hvor brukeren er i appen (eiendom, kontrakt)
- **Tre moduser:** Enkel (rask, én AI-kall), Avansert (full flyt med verktøy), Fullverdig (under utvikling)
- **Verktøy:** Søk i dokumenter, Lovdata, SQL-analyse, eiendomssøk, risikovurdering
- **Kilder:** Klikkbare lenker til eiendommer, kontrakter, dokumenter og eksterne kilder
- **Agent-graf (LangGraph):** Supervisor → Guardian → Researcher → Analyst → Writer

---

## 4. Datamodell og nøkkeltabeller

| Tabell | Beskrivelse |
|--------|-------------|
| properties | Eiendommer |
| units | Enheter (leiligheter, lokaler) |
| contracts | Kontrakter |
| parties | Parter (leietakere, eiere) |
| deviations | Avvik (FDV) |
| risk_assessments | Risikovurderinger |
| internal_control_cases | Internkontroll-saker |
| checklist_templates | Sjekklistemaler |
| budget | Budsjett per eiendom, år, måned |
| query_library | Lagrede SQL-mønstre for KI-Kollega |

---

## 5. Metodikk og beregninger

### 5.1 Risikovurdering

- Modell: R ≈ P × C (proxy-indikatorer, ikke faktisk forventet tap)
- Ekstern risiko: Bygningsalder, areal, NVE-nærhet, flomvarsel
- Operasjonell risiko: Åpne avvik (10 poeng per avvik, +10 for tiltaksfase)
- Statuskategorier: Kritisk (>75), Høy (>40), Moderat (>0), Lav (0)

### 5.2 Kostnadsanalyse

- Ratioer: kategori_sum / annual_rent
- Vurderingsgrenser: KRITISK (>3,0), HØY (>2,0), MODERAT (>1,5), NORMAL
- Kostnadskategorier: property, operations, investment, other

### 5.3 Prioriteringsindeks

- Prioritet = R_score × Årskostnad × Kritikalitetsfaktor
- Reservefaktor per risikotier (topp 10 %, midtsjikt, lav risiko)
- Styringsklasser: A (husleie), B (drift), C (investeringer), D (uforutsette)

---

## 6. Brukergrupper og tilganger

- **Brukere:** Innlogging via Credentials eller Google
- **Admin:** Brukeradministrasjon, teknisk dokumentasjon, import, HMS-kalender
- **Superbruker:** Full tilgang inkl. impersonasjon

---

## 7. Deploy og drift

- **Frontend:** Auto-deploy ved push til main (Vercel)
- **Backend:** Auto-deploy ved push til main (Railway) eller manuelt
- **Database:** Migrasjoner via Alembic
- **Secrets:** SECRET_KEY/NEXTAUTH_SECRET må være identiske på backend og frontend

---

## 8. Avhengigheter og forutsetninger

- Node.js 18+, Python 3.11+, PostgreSQL
- OPENAI_API_KEY for KI-Kollega
- NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN for kart
- DATABASE_URL (Supabase)
- NEXTAUTH_SECRET / SECRET_KEY for autentisering

---

## 9. Begrensninger og antakelser

- Risikoscoren er en **prioriteringsindikator**, ikke estimat av forventet tap
- Budsjettet er **syntetisk**, ikke godkjent budsjett
- Kostnadsanalysen forutsetter årlige tall; flerårige utgifter kan gi skjeve ratioer
- KI-Kollega Fullverdig modus er under utvikling

---

*Dokumentet beskriver løsningen slik den er implementert. Ved endringer i arkitektur eller funksjonalitet bør denne beskrivelsen oppdateres.*
