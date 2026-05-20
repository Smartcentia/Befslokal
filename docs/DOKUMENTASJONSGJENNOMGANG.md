# Dokumentasjonsgjennomgang – BEFS/KNOWME

**Dato:** 18. mars 2025  
**Formål:** Sammenligne brukerhjelp og dokumentasjon mot faktisk implementasjon i kodebasen.

**Oppdatert status (9. apr. 2026):** `docs/BRUKERHJELP.md` er utvidet med blant annet navigasjon, Innboks (`/innboks`), Jira, Institusjoner, Analyse & Innsikt, Kontroll 2027, Konkursovervåkning, full porteføljeliste (`/oversikt`), Agresso-sti (`/agresso-csv`), tilgjengelighet/personvern, oppdaterte **SSB**- og **Økonomi**-faner, samt utdyping av dashboard-widgeter. Tabellen under i §1.1 reflekterer fortsatt gjennomgangen per mars 2025; mange av punktene er nå dekket i brukerhjelpen.

---

## 1. BRUKERHJELP.md – Mangler og avvik

### 1.1 Sider/funksjoner som MANGLER i brukerhjelpen

| Funksjon | Rute | Beskrivelse | Prioritet |
|----------|------|-------------|-----------|
| **Institusjoner** | `/institusjoner` | Barnevernsinstitusjoner – kapasitetsoversikt (GK-plasser, budsjetterte plasser, kostnad per plass). Finnes i sidebaren under DRIFT & VEDLIKEHOLD. | Høy |
| **Innboks** | `/inbox` | Varsler fra internkontroll. Finnes i HOVEDMENY. | Høy |
| **Jira-integrasjon** | `/jira` | Opprett Jira-issues (KAN-prosjekt) direkte fra BEFS. Finnes i APP-seksjonen. | Medium |
| **Konkursovervåkning** | `/konkurs-monitor` | Admin: Overvåk leverandører/parter for konkursstatus. Finnes i admin-sidebaren. | Høy |
| **Oversikt** | `/oversikt` | Dataoversikt (eiendommer, avdelinger, kontrakter, leietakere). Ikke i sidebaren – kan være skjult/legacy. | Lav |
| **Tilgjengelighet** | `/tilgjengelighet` | Tilgjengelighetserklæring (UU). Lenkes fra Hjelp-siden. | Lav |
| **Personvern** | `/personvern` | Behandling av personopplysninger. Lenkes fra Hjelp-siden. | Lav |
| **Ordliste** | `/governance/glossary` | Begrepskatalog. | Lav |

### 1.2 Dashboard – manglende/ufullstendig beskrivelse

**Nåværende:** BRUKERHJELP nevner "Dashboard-varianter: Standard, Cyberpunk, Minimalist, Terminal eller Nordic."

**Mangler:**
- **Nye oppdateringer-panel:** Viser "siste aktivitet" og "kontrakter som utløper innen 90 dager". Ikke nevnt.
- **Kritiske Avvik:** Panel med åpne saker (critical/high). Ikke nevnt.
- **Activity Wheel:** Årshjul/aktivitetsoversikt. Ikke nevnt.
- **Eiendomsforvalter-dashboard:** Når bruker har rolle PROPERTY_MANAGER vises "Mine Eiendommer" i stedet for standard dashboard. Ikke nevnt.

### 1.3 SSB Statistikk – faner stemmer ikke

**BRUKERHJELP sier:**
- Søk i tabeller
- Populære tabeller
- Om SSB-integrasjonen
- Historiske indekser

**Faktisk implementasjon (4 faner):**
- **Søk tabeller** – søk i SSB Statbank
- **Hent data** – hent data fra valgt tabell
- **Kombiner med BEFS** – samstill SSB-data med BEFS-regnskap
- **Analyser og rapporter** – KI-basert analyse

Dokumentasjonen bør oppdateres til å matche de faktiske fanene.

### 1.4 Økonomi og Finans – faner sterkt utvidet

**BRUKERHJELP sier:** "Regional Oversikt", "Leverandørstatistikk", "Kostnadsmønstre".

**Faktisk implementasjon (10+ faner):**
- Overview (regional oversikt)
- Leverandører (suppliers)
- Katalog (catalog)
- Fakturaer (invoices)
- Mønstre (patterns)
- GL per eiendom (gl-per-property)
- Mangler kostnader (missing-costs)
- Kostnader uten eiendom (costs-without-property)
- Kontraktsoversikt pivot (contracts-pivot)
- Transaksjoner (transactions)

Brukerhjelpen dekker kun 3 av 10+ faner.

### 1.5 Admin & Verktøy – mangler flere verktøy

**BRUKERHJELP nevner:** Ekstern Risiko, Risikobildet, Finansiell Analyse, Rollesimulering, HMS Kalender, Brukeradministrasjon.

**Admin-dashboard har i tillegg:**
- Geokoding av adresser
- Bruker Impersonering (impersonate)
- Innkjøpsanalyse
- Økonomidata
- Data Import
- Dokumentarkiv
- Admin Håndbok
- Systemlogger
- Begrepskatalog Scan
- Kontraktskostnader
- **Konkursovervåkning** (via sidebaren, ikke admin-kort)

### 1.6 Analyse & Innsikt – ikke dokumentert

Siden **Analyse & Innsikt** (`/analysis`) gir tilgang til KI-drevne analysemoduler:
- Geografiske analyser
- Kontraktsanalyser
- Avviksanalyser
- Risikoanalyser
- Vedlikeholdsanalyser
- PDF-baserte analyser

Ikke nevnt i BRUKERHJELP.

### 1.7 FullScreenMenu – avvik fra sidebaren

FullScreenMenu (mobil/hurtigmeny) mangler bl.a.:
- Institusjoner
- Innboks
- Jira
- Konkursovervåkning
- Analyse & Innsikt
- Aktivitetshub
- Kalender

---

## 2. Help Center / Help API

Help-servicen (`help_service.py`) parser **BRUKERHJELP.md** og deler den inn i seksjoner basert på `## `-overskrifter. Innholdet i appen kommer altså direkte fra BRUKERHJELP.md.

**Konsekvens:** Alle mangler og avvik i BRUKERHJELP.md påvirker også det brukere ser i Hjelp-siden i appen.

---

## 3. AGENTS.md vs. CLAUDE.md – Deploy-instruksjoner

| Aspekt | AGENTS.md | CLAUDE.md | Korrekt |
|--------|-----------|-----------|---------|
| Backend deploy | `cd backend && railway up --detach` | `cd /path/to/BEFS_CLEAN && railway up --detach` | **CLAUDE.md** |
| Frontend deploy | Fra repo root | Fra repo root | Begge |

**CLAUDE.md** er korrekt: Railway-prosjektet `striking-insight` er koblet til repo root. Deploy fra `backend/` går til et annet prosjekt (`lovely-bravery`).

**Anbefaling:** Oppdater AGENTS.md til å bruke repo root for backend-deploy.

---

## 4. Andre dokumentfiler – status

| Dokument | Status |
|----------|--------|
| BUDSJETT_2026_ESTIMERING.md | Oppdatert – tall og metodikk stemmer |
| MASTER_REGNSKAP.md | Oppdatert – budsjett 2026, datakilder |
| INSTITUSJONS_CSV_TIL_DATABASE_VERIFISERING.md | Teknisk – verifisering av CSV-felter |
| LEVERANDOR_RISIKO.md | Referert fra BRUKERHJELP – instruks for leverandørkontroll |

---

## 5. Anbefalte tiltak (prioritert)

### Høy prioritet
1. **Legg til Institusjoner** – Ny seksjon i BRUKERHJELP om Barnevernsinstitusjoner-siden.
2. **Legg til Innboks** – Beskriv varsler fra internkontroll.
3. **Legg til Konkursovervåkning** – Under Admin & Verktøy.
4. **Oppdater SSB-faner** – Endre til: Søk tabeller, Hent data, Kombiner med BEFS, Analyser og rapporter.

### Medium prioritet
5. **Utvid Dashboard-seksjonen** – Nye oppdateringer, Kritiske Avvik, Activity Wheel, Eiendomsforvalter-dashboard.
6. **Utvid Økonomi og Finans** – Dokumenter de viktigste fanene (overview, suppliers, patterns, missing-costs, gl-per-property, contracts-pivot).
7. **Legg til Jira** – Kort beskrivelse under APP/Verktøy.
8. **Utvid Admin & Verktøy** – Geokoding, Innkjøpsanalyse, Økonomidata, Data Import, Dokumentarkiv, Kontraktskostnader, Begrepskatalog Scan.

### Lav prioritet
9. **Legg til Analyse & Innsikt** – Beskriv KI-analysemodulene.
10. **Oppdater AGENTS.md** – Backend deploy fra repo root.
11. **FullScreenMenu** – Vurder å legge til manglende lenker (Institusjoner, Innboks, m.m.).

---

## 6. Sider uten dokumentasjon (oversikt)

| Rute | Tittel | I sidebaren? |
|------|--------|--------------|
| / | Hjem | (root) |
| /dashboard | Oversikt | Ja |
| /inbox | Innboks | Ja |
| /properties | Eiendommer | Ja |
| /contracts | Kontrakter | Ja |
| /tenants | Leietakere | Ja |
| /parties/[id] | Partdetalj | (via tenants) |
| /checklists | Sjekklister | Ja |
| /deviations | Avvikshåndtering | Ja |
| /activities/hub | Aktivitetshub | Ja |
| /calendar | Kalender | Ja |
| /financials | Økonomi | Ja |
| /analysis | Analyse & Innsikt | Ja |
| /risk | Risikoanalyse | Ja |
| /institusjoner | Institusjoner | Ja |
| /bup-locations | BUP-lokasjoner | Ja |
| /lovdata-search | Lovdata-søk | Ja |
| /ssb | SSB Statistikk | Ja |
| /media-monitor | Media Overvåkning | Ja (admin) |
| /konkurs-monitor | Konkursovervåkning | Ja (admin) |
| /lab | AI Research Lab | (via FullScreenMenu) |
| /help | Hjelp & Dokumentasjon | Ja |
| /settings | Innstillinger | Ja |
| /jira | Jira | Ja |
| /oversikt | Oversikt | Nei |
| /tilgjengelighet | Tilgjengelighet | (via help) |
| /personvern | Personvern | (via help) |
| /governance/glossary | Ordliste | (via Data Governance?) |

---

*Rapport generert ved gjennomgang av frontend-ruter, Sidebar.tsx, FullScreenMenu.tsx, admin-sider, financials-faner, SSB-komponenter og docs/BRUKERHJELP.md.*
