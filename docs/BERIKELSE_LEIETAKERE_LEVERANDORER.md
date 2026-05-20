# Berikelse: Leietakere og leverandører

## Hva vi har bygget

### Scripts som beriker partier (leietakere/utleiere)

| Script | Hva det gjør |
|--------|---------------|
| `backend/app/scripts/enrich_parties_brreg_by_orgnr.py` | Henter BRREG-enhet + roller for alle partier med orgnr. Lagrer `brreg_enhet`, `brreg_roller` og uttrukket `roles` (daglig leder, styreleder, revisor). Gir også stiftelsesdato, næringskode (NACE). |
| `backend/app/scripts/enrich_parties_openai_company.py` | **Web-søk + OpenAI:** Søker på nettet etter firma (navn + orgnr), sender snippeter til OpenAI og lagrer en firmaoppsummering i `party.external_data["openai_company_summary"]` (tilsvarende det du får fra f.eks. Gemini: oversikt, roller, eierskap, økonomi, datterselskap). Krever `OPENAI_API_KEY`. |
| `backend/scripts/import_landlords.py` | Importerer/oppdaterer utleiere fra fil; kan sette orgnr på partier (som deretter kan berikes med BRREG). |

**Kjør BRREG-berikelse:**  
- **Fra prosjektrot (enklest):** `./scripts/kjor_enrich_parties_brreg.sh` (eller `--dry-run` for kun rapport).  
- **Fra backend-mappen:** `cd backend` og deretter `python3 -m app.scripts.enrich_parties_brreg_by_orgnr`. *(Kommandoen må kjøres fra `backend/` fordi modulen `app` ligger der – ellers får du «No module named 'app'».)*

**Kjør OpenAI-firmaoppsummering (web-søk + OpenAI, tilsvarer Gemini-oppsummering):**  
- **Fra prosjektrot:** `./scripts/kjor_enrich_parties_openai.sh` (eller `--dry-run` for kun rapport, `--limit 5` for å berike bare 5 partier). Krever `OPENAI_API_KEY` i miljøet.  
- Partysiden viser oppsummeringen under «Firmaoppsummering (AI)» når `external_data.openai_company_summary` er satt.  
- **Produksjon (Railway):** Knappen «Hent firmaoppsummering fra nettet» på partysiden krever at **OPENAI_API_KEY** er satt i Railway-miljøet. Gå til [Railway Dashboard](https://railway.app) → din backend-tjeneste → **Variables** → legg til `OPENAI_API_KEY` med din OpenAI-nøkkel, deretter **Deploy** eller vent på ny deploy.  
- **Mer BRREG på kortet:** Etter BRREG-berikelse viser partysiden nå også stiftelsesdato, næring (NACE), daglig leder, styreleder og revisor (hentet fra BRREG roller).

### Scripts som beriker eiendommer (leie/vedlikehold – ikke Partier)

| Script | Hva det gjør |
|--------|---------------|
| `backend/scripts/finn_og_fyll_leie_vedlikehold.py` | Fyller `property.external_data.financials` med leie/vedlikehold (syntetisk eller fra regnskap). Påvirker **eiendom**, ikke Partier. |
| `backend/scripts/import_and_synthesize.py` | Importerer/syntetiserer utgifter per eiendom (manual_expenses med `provider`/`type`). |
| Diverse import_enrichment_*.py | Fyller eiendomsdata (region, areal, osv.). |

Leverandørstatistikk (Økonomi-siden, «Top Leverandører») bygges fra **eiendommenes** `external_data.financials.manual_expenses[].provider` – altså strenger fra utgiftslinjer, ikke fra Party-tabellen.

---

## Hvorfor viste ikke leietaker-kortet berikelse?

**Årsak:** BRREG-scriptet lagrer data **kun** under `party.external_data["brreg_enhet"]` (objekt med `email`, `phone`, `address`, `source`). Leietaker-kortet (siden «Leietakere») leste derimot fra **toppnivå**: `external_data.email`, `external_data.phone`, `external_data.address`, `external_data.source`. Siden disse aldri ble satt på toppnivå, ble ingenting vist.

**Løsning:** Leietaker-siden er oppdatert til å lese fra `external_data.brreg_enhet` som fallback (samme logikk som partydetaljsiden `/parties/[id]`). Da vises e-post, telefon, adresse og BRREG-merkelapp på kortet når partiet er beriket med `enrich_parties_brreg_by_orgnr`.

---

## Hvorfor vises N/A på partykortet (e-post, telefon, adresse)?

Når partydetaljsiden (f.eks. «Narvikgården utleiebygg AS») viser **EMAIL: N/A**, **PHONE: N/A**, **POSTAL ADDRESS: N/A**, skyldes det én av disse to tingene:

### 1. BRREG-berikelse er ikke kjørt (eller partiet ble lagt til etter siste kjøring)

Kortet henter kontaktinfo fra `party.external_data.brreg_enhet` (som settes av scriptet `enrich_parties_brreg_by_orgnr`). Hvis scriptet **aldri har kjørt** for denne part, eller partiet ble opprettet **etter** siste kjøring, finnes det ingen `brreg_enhet` – og da faller vi tilbake til `party.contact_email` / `party.contact_phone` / `party.address`. Hvis også disse er tomme, vises **N/A**.

**Løsning:** Kjør BRREG-berikelse slik at alle partier med orgnr får hentet og lagret data:

```bash
# Fra prosjektroten (BEFS_CLEAN) – anbefalt:
./scripts/kjor_enrich_parties_brreg.sh

# Eller fra backend-mappen:
cd backend
python3 -m app.scripts.enrich_parties_brreg_by_orgnr
```

(Kun rapport uten å skrive til DB: `./scripts/kjor_enrich_parties_brreg.sh --dry-run`. På Mac: bruk `python3`, ikke `python`.)

### 2. BRREG har faktisk ikke kontaktinfo for denne enheten

Enhetsregisteret (data.brreg.no) returnerer **kun det som er registrert**. Mange foretak har **ikke** e-post eller telefon i BRREG – da setter vår BRREG-tjeneste eksplisitt `"N/A"` for `email` og `phone`. Adresse (forretningsadresse/postadresse) finnes ofte; hvis også den mangler i BRREG, blir adresse N/A.

**Løsning:**  
- Sjekk enheten manuelt på [Brønnøysundregistrene](https://www.brreg.no/): Søk på orgnr 992843012 – hvis e-post/telefon ikke står der, kan vi ikke «finne opp» data.  
- **Manuell overstyring:** Fyll inn `contact_email`, `contact_phone`, `address` direkte på partiet i databasen eller via en redigeringsside – da vises disse i stedet for N/A (partydetaljsiden bruker allerede `party.contact_email` osv. som fallback).

---

## Hvorfor vises ikke berikelse på «leverandørkort»?

**Leverandørlisten** (Økonomi → Leverandørstatistikk, og «Top Leverandører» på dashboard) er **utgiftsbasert**:

- Data kommer fra `property.external_data.financials.manual_expenses[]`.
- Hver linje har `provider` (leverandørnavn som streng) og `type` (kategori).
- Det finnes **ingen kobling** mellom disse navnene og `Party`-tabellen (party_id/orgnr).

Derfor kan vi ikke vise Party-berikelse (BRREG, kontaktinfo) på leverandørkortene uten å innføre en **kobling** leverandørnavn → Parti (f.eks. ved å matche på navn/orgnr og vise berikelse for den matchende part).

---

## Informasjon fra internett (web-søk)

Vi hadde også lagt inn at systemet skal kunne **finne informasjon på internett** – som «berikelse» av svar (markedsleie, praksis, nyheter):

- **KI Kollega (AGENT.md):** Beskriver at kollegaen har tilgang på «både interne data og internett» og skal bruke **eksterne kilder** for kontekst (f.eks. «Vår energikostnad er X (intern), hvordan ligger dette an mot markedspris (ekstern)?»). Verktøy som er nevnt: `search_web`, `fetch_web_content`.
- **Researcher-node (agent-flyt):** Når dokumenter/DB ikke gir treff, prøver den **web search** som fallback (`search_web_tool`) før den ruter til analyst.
- **MCP-handler:** `search_web` bruker nå **DuckDuckGo** (pakken `duckduckgo-search`). `fetch_web_content` henter URL og kan ingest i RAG.

**Status:** Web-søk er på plass. DuckDuckGo brukes fordi vi kan bruke alt av Google *unntatt* API – dermed ingen Google Custom Search API-nøkkel. Ingen egen API-nøkkel trengs for DuckDuckGo.

---

## Oppsummering

| Område | Berikelse | Vises på kort? |
|--------|------------|----------------|
| **Leietakere** (Parter med orgnr) | `enrich_parties_brreg_by_orgnr` → `external_data.brreg_enhet` | **Ja** (etter fiks: kort leser nå fra `brreg_enhet`) |
| **Partydetalj** `/parties/[id]` | `brreg_enhet` + `roles` (daglig leder, styreleder, revisor) + stiftelsesdato, næring (NACE) + evt. `openai_company_summary` | Ja – viser kontaktinfo, roller, stiftelsesdato, næring, og «Firmaoppsummering (AI)» når OpenAI-berikelse er kjørt |
| **OpenAI firmaoppsummering** | `enrich_parties_openai_company` → web-søk + OpenAI → `external_data.openai_company_summary` | Ja – vises som egen seksjon på partysiden (tilsvarer oppsummering fra f.eks. Gemini) |
| **Leverandørstatistikk** | Bygges fra utgiftslinjer (`provider`), ikke Party | Nei – ingen Party-kobling; berikelse kan legges til ved matching mot Party |
| **Informasjon fra internett** | KI Kollega: `search_web` (DuckDuckGo) + `fetch_web_content` (AGENT.md, Researcher-node) | **På plass:** `search_web` bruker DuckDuckGo (uten API-nøkkel); `fetch_web_content` henter URL og kan ingest i RAG |
