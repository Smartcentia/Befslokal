# DPIA: Personvernkonsekvensutredning for BEFS (Boenhetsforvaltningssystem)

| Dokumentinformasjon | Detaljer |
| :--- | :--- |
| **Dato** | 07.02.2026 |
| **Versjon** | 1.0 |
| **Status** | Utkast |
| **Ansvarlig** | Frank Vevle (Produkteier) |
| **Revisjon** | 07.05.2026 (Kvartalsvis) |

---

## 1. Beskrivelse av behandlingen
*En systematisk beskrivelse av den planlagte behandlingen og formålene.*

### 1.1 Formål
Hva er hovedformålet med løsningen?
> Applikasjonen (BEFS) skal effektivisere forvaltningen av eiendomsporteføljen ved å samle informasjon om eiendommer, leiekontrakter, leietakere, vedlikehold og bygningsteknologiske data (IoT) i ett system. Systemet skal også forenkle kommunikasjon med leietakere og støtte økonomisk oppfølging.

### 1.2 Systemarkitektur og Dataflyt
Beskriv kort hvordan data beveger seg gjennom systemet.
* **Datakilder:**
  * Brukerinput (Administratorer, Driftsansvarlige, Leietakere)
  * Importerte data (Kontrakter, eiendomsinfo)
  * IoT-enheter (Sensorer for temperatur, energi, tilgangskontroll)
  * API-integrasjoner (Potensielt økonomisystem, HR)
* **Lagring:** Supabase Database (PostgreSQL) - Managed Service.
* **Datamottakere:**
  * Interne avdelinger (Økonomi, Drift, HR)
  * Eksterne leverandører (Vaktmestertjenester - kun relevant bestillingsdata)
  * Leietakere (Egne data via "Min Side")

**Konseptuell Dataflyt:**

```mermaid
graph TD
    User[Bruker / Leietaker] -->|HTTPS (Auth)| FE[Frontend (Next.js)]
    IoT[IoT Sensorer] -->|MQTT / HTTPS| GW[IoT Gateway]
    GW -->|API| BE[Backend API (FastAPI)]
    FE -->|REST API| BE
    BE -->|SQL (Kryptert)| DB[(PostgreSQL Database)]
    BE -->|Vektorsøk| AI[AI Service & RAG Context]
    BE -->|OIDC| IDP[Identity Provider (NextAuth)]
```

### 1.3 Kategorier av personopplysninger
Hvilke typer data behandles? Kryss av eller fyll ut:
- [x] **Alminnelige personopplysninger:** Navn, e-post, telefonnummer, adresse (Leietakere, Ansatte, Kontaktpersoner).
- [x] **Finansielle data:** Kontonummer (utbetaling), leiekontrakter, betalingsstatus, fakturagrunnlag.
- [ ] **Særlige kategorier (Sensitive data):** Ingen planlagt behandling av helseopplysninger eller andre sensitive kategorier (GDPR Art 9).
- [x] **Tekniske spor:** IP-adresser, innloggingslogger, systemlogger, sensor-metadata (om det kan kobles til person).

---

## 2. Vurdering av nødvendighet og proporsjonalitet
*Hvorfor er det nødvendig å behandle disse dataene?*

* **Rettslig grunnlag:**
  * **Nødvendig for avtale (GDPR Art 6.1.b):** Behandling av kontraktinformasjon og kontaktinfo for å oppfylle leieforholdet.
  * **Rettslig forpliktelse (GDPR Art 6.1.c):** Lagring av data iht. Bokføringsloven (5 år).
  * **Berettiget interesse (GDPR Art 6.1.f):** Sikkerhetslogging, drift av IoT-sensorer for energioptimalisering.
* **Dataminimering:**
  * Vi har implementert dataklassifisering i applikasjonen for å synliggjøre hvilke data som samles inn.
  * Kun nødvendig data for forvaltning lagres (trenger f.eks. ikke fødselsnummer hvis ikke strengt nødvendig for kontrakt/kredittsjekk - per nå lagres dette minimalt).
* **Lagringstid:**
  * **Aktive kontrakter:** Lagres så lenge avtaleforholdet består.
  * **Regnskapsdata:** 5 år ihht. bokføringsloven.
  * **Logger/Spor:** Overskrives iht. rotasjonspolitikk (f.eks. 90 dager for aktivitetslogger).
  * **Avsluttede brukere:** Slettes eller anonymiseres innen 30 dager etter avslutning.

---

## 3. Risikovurdering (Sikkerhetsanalyse)
*Vurdering av risiko for de registrertes rettigheter og friheter.*

**Skala:** 1 (Lav) til 5 (Høy). **Risiko = Sannsynlighet x Konsekvens.**

| Risiko-scenario | Sannsynlighet (1-5) | Konsekvens (1-5) | Risikonivå | Beskrivelse av konsekvens |
| :--- | :---: | :---: | :---: | :--- |
| **Uautorisert tilgang** (Hacking/Konto-tyveri) | 2 | 5 | **10 (Høy)** | Sensitive data (kontrakter, personalia) kommer på avveie. ID-tyveri risiko. Omdømmetap. |
| **Feil tilgangsstyring** (Intern tilgang) | 3 | 4 | **12 (Høy)** | Ansatte ser data de ikke skal (f.eks. andre leietakeres kontrakter). Personvernbrudd. |
| **Datatap** (Systemfeil/Sletting) | 1 | 4 | **4 (Lav)** | Tap av historikk og kontrakter. Økonomisk konsekvens og merarbeid. |
| **Lekkasje via AI** (Prompt-injeksjon) | 2 | 3 | **6 (Medium)** | AI-assistent utleverer info om bruker A til bruker B ved feil kontekst-isolering. |
| **IoT-sårbarhet** (Sensor-hacking) | 2 | 2 | **4 (Lav)** | Manipulering av temperaturdata eller adgangskontroll. Påvirker fysisk sikkerhet/komfort. |

---

## 4. Tiltak for å håndtere risiko
*Hvilke tekniske og organisatoriske tiltak er implementert for å redusere risikoene identifisert over?*

### 4.1 Tekniske tiltak
- [x] **Kryptering:** Data krypteres "at rest" (i Supabase/Postgres) og "in transit" (TLS 1.2+).
- [x] **Tilgangskontroll:** Rollebasert tilgangskontroll (RBAC) implementert i Backend (FastAPI dependency injection).
- [x] **Rad-nivå sikkerhet:** (Planlagt/Påbegynt) Filtrering av data basert på `organization_id` eller `user_id` i alle spørringer.
- [x] **Autentisering:** Bruk av sikker OAuth2/OpenID Connect via NextAuth (støtter MFA ved behov).
- [x] **Logging:** Systemrevisjonsspor (Audit logs) for sensitive operasjoner (sletting, endring av tilgang).
- [x] **Backups:** Automatiserte backups via skytjeneste (Supabase) med Point-in-Time Recovery (PITR).
- [ ] **AI-Sikkerhet:** Input-sanitering for RAG og skille mellom brukerkontekster i vektorsøk.

### 4.2 Organisatoriske tiltak
- [x] **Dataklassifisering:** Egen modul i verktøyet for å merke data med sensitivitet og eierskap.
- [ ] **Opplæring:** Sikkerhetsopplæring for utviklere og systemadministratorer.
- [ ] **Code Review:** Pull Requests kreves for endringer i master-branch.
- [ ] **Databehandleravtaler:** Supabase (DB), Vercel/Hosting (Frontend) og evt. AI-provider må ha gyldige DPA-er.

---

## 5. Konklusjon
*Samlet vurdering av restrisiko etter at tiltak er innført.*

Er restrisikoen akseptabel?
- [x] **Ja, risikoen anses håndtert per nå.** (Gitt at påbegynte tiltak fullføres før produksjonssetting).
- [ ] **Nei, vi må innføre flere tiltak.**
- [ ] **Uavklart.**

**Signert:**
__________________________
Frank Vevle
Produkteier / Ansvarlig
