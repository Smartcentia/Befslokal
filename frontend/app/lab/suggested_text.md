# Forslag til tekster for AI Research Lab

## DEKOMPONERING

### Tittel
**Intelligent verktøygenerering med selvhelbredende kode**

### Beskrivelse
Systemet analyserer komplekse forespørsler, genererer Python-verktøy automatisk, og validerer dem i et isolert sandbox-miljø. Ved feil aktiveres selvhelbredende mekanismer som retter koden før den lagres i det globale verktøybiblioteket.

### Eksempel på forespørsel
*"Lag et verktøy som analyserer Q3-salgsdata fra Europa vs Asia og identifiserer trender for neste kvartal."*

### Datapunkter som vises
- Q3-data Europa
- Q3-data Asia  
- Historiske trender
- Markedsprediksjoner

---

## RAG-ARKITEKTUR

### Tittel
**Fra dokumenter til validerte svar med hybrid søk**

### Beskrivelse
Kombinerer semantisk søk (vektorembeddings) med fulltekstsøk for å hente relevante dokumenter. Systemet validerer kilder, rangerer resultater etter relevans, og genererer svar med kildehenvisninger. Støtter både interne dokumenter og eksterne kilder som Lovdata.

### Eksempel på flyt
1. **Brukerforespørsel** → "Hva sier husleieloven om indeksregulering?"
2. **Hybrid søk** → Finner relevante lovtekster og interne retningslinjer  
3. **Validering** → Sjekker kildens autoritet og aktualitet
4. **Svar** → Genererer strukturert svar med lenker til lovdata.no

---

## FINANCIAL QUERY PANEL

### Tittel  
**Naturlig språk til SQL-analyse**

### Beskrivelse
Oversetter spørsmål på norsk til SQL-spørringer mot PostgreSQL-databasen. Analyserer eiendommer, kontrakter, kostnader og nøkkeltall. Resultater presenteres som strukturerte tabeller med mulighet for eksport og visualisering.

### Eksempel på spørsmål
- "Hvor mange m² leier vi totalt i Region Øst?"
- "Hvilke kontrakter utløper i løpet av 6 måneder?"
- "Hva er gjennomsnittlig kostnad per m² for familievernkontor?"

---

## JIRA INTEGRATION

### Tittel
**Opprett oppgaver direkte fra AI-samtaler**

### Beskrivelse  
Når brukeren ber om å lage en oppgave, registrere et avvik eller opprette en to-do, kan AI-assistenten automatisk opprette Jira-saker med riktig prosjekt, type og beskrivelse. Returnerer lenke til den opprettede saken.

### Eksempel på bruk
**Bruker:** "Lag en oppgave for å sjekke ventilasjonssystemet på Vestlund"  
**AI:** ✅ Opprettet Jira-sak: **[KAN-123] Sjekk ventilasjonssystem Vestlund**  
Lenke: https://jira.example.com/browse/KAN-123

---

## TOOL LIBRARY

### Tittel
**Delt verktøybibliotek med QA-validering**

### Beskrivelse
Alle genererte verktøy lagres i et globalt bibliotek med semantisk søk. Verktøy går gjennom automatisk QA-testing før de publiseres. Brukere kan "pinne" ofte brukte verktøy for raskere tilgang.

### Statuser
- 🟣 **QA Analyzing...** - Verktøyet testes automatisk
- 🔴 **QA Failed** - Feil oppdaget, må rettes  
- 🟢 **Verified** - Godkjent og klar til bruk
- 🟡 **Experimental** - Fungerer, men ikke fullt validert

---

## KI KOLLEGA (AI Assistant)

### Tittel
**Kontekstbevisst AI-assistent med tilgang til alle systemer**

### Beskrivelse
Integrert AI-assistent som forstår brukerens kontekst (hvilken side, eiendom, kontrakt osv.) og har tilgang til:
- **Dokumentsøk** - Rutiner, instrukser, HMS-krav
- **Database** - Eiendommer, kontrakter, parter, komponenter  
- **Lovdata** - Lover og forskrifter
- **Risikovurdering** - Flom, grunnforhold, miljø (NVE, Kartverket)
- **Jira** - Oppgaveopprettelse
- **FDV-data** - Bygningskomponenter og utstyr

### Eksempel på samtale
**Bruker:** "Hvilke familievernkontor har vi i Oslo?"  
**AI:** Fant 3 eiendommer:
- Familievern Oslo Sentrum (Storgata 12)
- Familievern Grorud (Grorudveien 45)  
- Familievern Søndre (Mosseveien 89)

**Bruker:** "Hva er risikovurderingen for Grorud?"  
**AI:** 🟡 **Moderat risiko (45/100)**
- 🌊 Flomfare: 30/100 (Lav)
- 🏔️ Grunnforhold: 60/100 (Moderat - kvikkleire i området)
- 🌱 Miljørisiko: 20/100 (Lav)

---

## TEKNISK ARKITEKTUR

### Backend
- **FastAPI** - REST API med async support
- **PostgreSQL** - Strukturerte data med pgvector for embeddings
- **OpenAI/Local AI** - LLM for naturlig språkforståelse
- **Jira API** - Oppgaveintegrasjon
- **MCP (Model Context Protocol)** - Modulær verktøyintegrasjon

### Frontend  
- **Next.js** - React-basert frontend med TypeScript
- **TailwindCSS** - Styling
- **Real-time updates** - WebSocket for live loggføring

### Sikkerhet
- **Sandbox-miljø** - Isolert kjøring av generert kode
- **Rollbasert tilgang** - Admin, Regional Manager, Property Manager, Janitor
- **API-logging** - Full audit trail av alle AI-kall
