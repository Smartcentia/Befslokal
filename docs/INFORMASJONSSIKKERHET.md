# Informasjonssikkerhet – BEFS / KNOWME

**Dokumenttype:** Løsningsbeskrivelse – informasjonssikkerhet  
**Versjon:** 1.0  
**Sist oppdatert:** Februar 2026

---

## 1. Oversikt

BEFS (Bufetat Eiendomsforvaltningssystem) er informasjonssikret gjennom flere lag: autentisering, brukerroller og tilganger, autorisasjon, CORS, sikker håndtering av hemmeligheter, og begrenset feilinformasjon i produksjon.

---

## 2. Autentisering (JWT)

- **NextAuth** med JWT (HS256) brukes for innlogging
- Tokens signeres med `SECRET_KEY` / `NEXTAUTH_SECRET` (må være identisk på frontend og backend)
- Backend validerer token med signatur, utløpstid og at e-post er gyldig
- Alle API-kall krever `Authorization: Bearer <token>` – unntatt noen få åpne endepunkter

---

## 3. AuthMiddleware – sentral sikkerhet

- Alle forespørsler går gjennom `AuthMiddleware`
- Kun disse stiene er åpne uten innlogging:
  - `/health`, `/api/v1/health`
  - `/api/v1/auth/send-verification-code`
  - `/api/v1/auth/verify-email`
  - `/api/v1/auth/verify-mfa`
- Alle andre endepunkter krever gyldig token, ellers returneres 401

---

## 4. Endepunkt-sikkerhet

- **AuthMiddleware** intercepterer alle requests og krever `Authorization: Bearer <token>` for alle endepunkter unntatt open paths
- Mange endepunkter bruker i tillegg `Depends(get_current_user)` for dobbel sikkerhet og tydelig dokumentasjon
- Ingen endepunkter utenom open paths er tilgjengelige uten gyldig token
- **Rate limiting** på åpne auth-endepunkter (send-verification-code, verify-email, verify-mfa): 10 forespørsler/min per IP
- **Sikkerhetsnivå:** Høy

*Detaljert analyse: [ENDPUNKT_SIKKERHET_ANALYSE.md](../dokumentasjon/ENDPUNKT_SIKKERHET_ANALYSE.md)*

---

## 5. CORS (Cross-Origin)

- CORS er begrenset til definerte origins fra konfigurasjon
- Regex for Vercel-preview: `https://.*\.vercel.app`
- Reduserer risiko for uønskede tredjepartsdomener

---

## 6. Hemmeligheter og konfigurasjon

- Ingen hemmeligheter hardkodet i kode
- Bruk av miljøvariabler: `SECRET_KEY`, `DATABASE_URL`, `OPENAI_API_KEY`, osv.
- Feilmeldinger i produksjon er generelle (f.eks. «Invalid authentication credentials») – ingen detaljer om signatur eller JWT lekkes
- **Global exception handler:** Returnerer kun «Internal server error» i produksjon – ingen stack traces eller feildetaljer til klient

---

## 7. Database

- PostgreSQL (Supabase) med SSL
- `DATABASE_URL` normaliseres og renses for uønskede parametere
- Migrasjoner kjøres via Alembic

---

## 8. Brukere, innlogging, roller og tilganger

### 8.1 Innlogging

- **Credentials** – e-post + passord (admin-e-poster godtas uten passord-sjekk mot backend – kun for intern bruk)
- **Google OAuth** – innlogging via Google-konto
- Ved første innlogging opprettes bruker automatisk i databasen med rolle basert på `ADMIN_EMAILS`

### 8.2 Brukerroller (UserRole)

| Rolle | Beskrivelse | Tilgang |
| :--- | :--- | :--- |
| **ADMIN** | Administrator | Alt – alle eiendommer og alle endepunkter |
| **REGIONAL_MANAGER** | Regionssjef | Eiendommer i sin region (`user.region`) |
| **PROPERTY_MANAGER** | Eiendomsforvalter | Kun tildelte eiendommer (via `user_property_association`) |
| **TENANT** | Leietaker | Kun tildelte eiendommer, **kun lesing** |

### 8.3 Tilgangskontroll

- **Admin-endepunkter** (`get_current_active_superuser`): `/api/v1/admin/*`, `/api/v1/import/*` – krever ADMIN
- **Eiendomstilgang** (`check_property_access`): Properties, Contracts, Units, Risk, Deviations, Internal Control, Files – filtrert etter rolle og tildeling
- **Impersonering:** Kun brukere i `ADMIN_EMAILS` kan impersonere andre; alle impersoneringer logges i audit

### 8.4 Dashboard for roller og tilganger

**Fullverdig implementert.** Admin-dashboardet (`/admin`) har:

- **Brukeradministrasjon** (`/admin/users`): Legg til, rediger, deaktiver brukere. Redigering av rolle, region og eiendomstildeling. Impersonering (Simuler) for testing.

### 8.5 Dataklassifisering og Governance

Systemet har et integrert **Data Classification Catalog** som definerer risikonivå for all lagret informasjon. Klassifiseringen følger tre nivåer:

| Nivå | Type | Beskrivelse | Eksempler |
| :--- | :--- | :--- | :--- |
| **L3** | **Restricted** | Svært sensitive data (PII, Finans, Hemmeligheter) | Passord-hasher, tokens, leiebeløp, fullstendige adresser, PII i logger |
| **L2** | **Internal** | Interne data med begrenset innsyn | Revisjonsspor (audit logs), deployment-logger, system-IDs |
| **L1** | **Public** | Offentlig eller er ikke-sensitiv intern info | Orgnr, bygningstekniske data, offentlige adresser, sensorverdier |

#### Sentrale klassifiserte domener

| Domene | Ansvarlig | Beskrivelse |
| :--- | :--- | :--- |
| **Identitet** | Frank Vevle | Brukerkontoer, MFA, sesjoner og tilganger (Primært L3) |
| **Økonomi** | Frank Vevle | Leiekontrakter, budsjett, utgifter og transaksjoner (L3) |
| **Eiendom** | Frank Vevle | Eiendomsregister, BIM-modeller, vedlikehold (L1-L3) |
| **AI & Data** | Frank Vevle | Spørrelogger, RAG-kontekst, agent-minne (L1-L3) |
| **Compliance** | Frank Vevle | Audit logs, GDPR-krav, risikovurderinger (L1-L3) |
| **System** | Frank Vevle | Miljøvariabler, deployment-metadata, migrasjoner (L1-L3) |

#### Detaljert tabell-katalog (Utdrag av L3-tabeller)

| Tabell | Domene | Beskrivelse | Risiko |
| :--- | :--- | :--- | :--- |
| `users` | Identity | Kjernebrukere, passord og roller | **L3** |
| `nextauth_accounts` | Identity | OAuth-koblinger (access_tokens) | **L3** |
| `contracts` | Finance | Leiekontrakter og betaling (JSONB mixed) | **L3** |
| `budget` | Finance | Budsjettdata per eiendom | **L3** |
| `query_logs` | AI | Brukerspørsmål til AI (kan inneholde PII) | **L3** |
| `environment_variables` | System | Applikasjonshemmeligheter | **L3** |
| `api_usage` | AI | Tokenbruk og kostnad per bruker | **L3** |

Fullstendig oversikt over alle 50+ tabeller og deres kolonne-klassifisering finnes i det visuelle **Data Governance Dashboard** i applikasjonen.

---

## 9. DPIA (Personvernkonsekvensutredning)

- **Bruker Impersonering** (`/admin/impersonate`): Filtrering på rolle/region, impersonering for testing.

**Tilgjengelig i UI:**

- Legg til bruker (e-post, navn, rolle, region, eiendommer)
- Redigering av brukerrolle, region og eiendomstildeling
- Soft delete (deaktivering) av brukere

---

## 10. KI-Kollega (AI)

- SQL-validering for å unngå uønskede spørringer
- Guardian-node i agent-grafen for sikkerhetskontroll
- Debug-endepunkt er fjernet/avskrudd i produksjon

---

## 11. Eksterne integrasjoner

- **BRREG:** Åpne data uten auth; beskyttede data (f.eks. RRH) krever Maskinporten
- **NVE, Kartverket, Lovdata:** API-er med egne sikkerhetsmodeller

---

## 12. Oppsummering

| Område | Tiltak |
| :--- | :--- |
| **Autentisering** | JWT med HS256 og delt hemmelighet |
| **Brukere/roller** | ADMIN, REGIONAL_MANAGER, PROPERTY_MANAGER, TENANT; eiendomstilgang via `user_property_association` |
| **Dashboard** | Fullverdig brukeradministrasjon: legg til, rediger, deaktiver; rolle, region, eiendomstildeling |
| **Endepunkt-sikkerhet** | AuthMiddleware på alle endepunkter, kun definerte open paths uten auth; rate limiting på auth-endepunkter |
| **Autorisasjon** | Middleware + rollekontroll |
| **CORS** | Begrenset til tillatte origins |
| **Hemmeligheter** | Kun via miljøvariabler |
| **Feilhåndtering** | Generelle feilmeldinger i produksjon |
| **Audit** | Logging av impersonering |
| **Database** | SSL og sikker tilkobling |

---

*Dokumentet beskriver informasjonssikkerheten slik den er implementert. Ved endringer i arkitektur eller sikkerhetstiltak bør denne beskrivelsen oppdateres.*
