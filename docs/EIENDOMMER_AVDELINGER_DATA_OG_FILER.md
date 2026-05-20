# Eiendommer og avdelinger – datakilder og filer

**Formål:** Detaljert forklaring av hvordan eiendommer har fått «avdelinger» (enhetstype og formål), hvilke data som brukes, og hvilke filer som er involvert.

**Sist oppdatert:** 3. februar 2026

---

## 1. Hva betyr «avdeling» her?

I BEFS brukes **avdeling** til å skille mellom:

| Felt | Betydning | Eksempelverdier |
|------|-----------|------------------|
| **Enhetstype** (kort) | Om enheten er en **avdeling under** en institusjon eller **hele institusjonen** | `Avdeling`, `Barnevernsinstitusjon` |
| **Formål (utledet)** | Hva enheten er – formål/type | `Barnevernsinstitusjon`, `Institusjonsavdeling`, `Omsorgssenter` |

- **Avdeling** = én avdeling under en større institusjon (f.eks. en boenhet eller et tilbud).
- **Barnevernsinstitusjon** = hele institusjonen som enhet.

Dette brukes blant annet til kostnadsfordeling: å fordele kostnader per eiendom og per avdeling/institusjon (jf. [MINNEFIL_KOSTNADSFORDELING_AVDELING.md](MINNEFIL_KOSTNADSFORDELING_AVDELING.md) § 26–28).

---

## 2. Hvilke data brukes?

### 2.1 Primær kilde: e-don2 / e-dom

Data kommer fra **enhetsregisteret** som leveres i filer med e-don2/e-dom-format:

| Kilde | Fil(er) | Beskrivelse |
|-------|---------|-------------|
| **e-don2** | `backend/e-don2.txt`, `backend/e-dom.txt`, `backend/e-don.txt`, `backend/e-dom2.txt` | TSV (tab-separert) eller semikolon. Én header, deretter én rad per enhet. |
| **e-dom (finans)** | `finans/e-dom.txt` | Samme kolonnestruktur – enhetsliste for barnevernsinstitusjoner og avdelinger. |

**Relevante kolonner for avdeling:**

| Kolonne i fil | Lagres i DB som | Innhold |
|---------------|-----------------|---------|
| **Enhetskorttype** | `unit_short_type` | `Avdeling` eller `Barnevernsinstitusjon` |
| **Enhetstype (Utledet)** | `unit_type_derived` | F.eks. `Barnevernsinstitusjon`, `Institusjonsavdeling`, `Omsorgssenter` |
| **EnhetID** | `unit_id_erp` | Unik enhets-ID (tall) – brukes til matching og til kobling mot regnskap (Dim1). |
| **Enhetsnavn** | `name` | Enhetens navn. |
| **Lokasjonskode** | `lokalisering_id` | Eiendoms-/lokasjonskode. |
| **Adresse**, **Postnummer**, **Poststed**, **Region**, **Kommune** | tilsvarende felter på Property | Brukes til å matche rad i filen mot eiendom i databasen. |

Andre kolonner (f.eks. Hjemler, Eierskapenhet, Antall budsjetterte plasser) importeres også og lagres på Property der det finnes felt.

### 2.2 Referanse: birk_og_plasser.csv

Filen **`finans/birk _og_plasser.csv`** har samme type informasjon (Enhetskorttype, Enhetstype Utledet, EnhetID, adresse) og brukes i prosjektet til **mapping og analyse** (f.eks. scriptet `finans/map_birk_og_plasser_to_portfeb.py`). **Import til BEFS-databasen** skjer imidlertid fra **e-don2/e-dom-filene** i `backend/`, ikke direkte fra birk_og_plasser.csv. Strukturen er lik: Enhetskorttype = Avdeling/Barnevernsinstitusjon, Enhetstype (Utledet) = formål.

---

## 3. Hvordan kobles en rad i e-don2 til en eiendom?

Importen (**e-don2-import**) matcher hver rad i e-don2/e-dom-filen mot eksisterende eiendommer i databasen. Den bruker **fire nivåer** (tiered matching):

1. **Eksakt Lokasjonskode** – radens `Lokasjonskode` = eiendommens `lokalisering_id`.
2. **Eksakt EnhetID** – radens `EnhetID` = eiendommens `unit_id_erp` (fra tidligere import).
3. **Eksakt adresse** – normalisert adresse fra rad = normalisert `address` på eiendom.
4. **Heuristisk adresse** – like adresser med synonyme suffiks (f.eks. gata/gaten, veien/vegen).
5. **Fuzzy adresse** – likhet (SequenceMatcher) mot adresse, med krav til score (≥ 0,85) og margin mot nest beste.
6. **Fuzzy navn** – likhet mot eiendommens navn dersom adresse ikke ga treff.

Når en rad **matcher** én eiendom, oppdateres den eiendommen med verdier fra raden – blant dem **Enhetskorttype** → `unit_short_type` og **Enhetstype (Utledet)** → `unit_type_derived`. Dermed «får» eiendommen avdeling/enhetstype fra e-don2-data som er knyttet til den via Lokasjonskode, EnhetID eller adresse.

---

## 4. Filer som er involvert

### 4.1 Backend – lagring og import

| Fil | Rolle |
|-----|--------|
| **`backend/app/domains/core/models/property.py`** | Property-modellen: kolonnene `unit_id_erp`, `unit_short_type`, `unit_type_derived` (linje 59–61). |
| **`backend/app/schemas/property.py`** | Pydantic-schema for API: samme felter eksponeres i JSON (linje 55–56). |
| **`backend/app/services/data_management.py`** | **`import_edon2_csv`**: leser e-don2/e-dom-innhold, normaliserer kolonnenavn (bl.a. `enhetskorttype` → `Enhetskorttype`, `enhetstype (utledet)` → `Enhetstype (Utledet)`), matcher rader mot eiendommer, og setter `prop.unit_short_type` og `prop.unit_type_derived` (linje 750–751). |
| **`backend/alembic/versions/20260203_add_edon2_unit_type_columns.py`** | Migrering som legger til kolonnene `unit_short_type` og `unit_type_derived` i tabellen `properties`. |
| **`backend/app/scripts/import_edon2_data.py`** | Script som leser `e-don2.txt`, `e-dom.txt` m.m. fra `backend/` og kaller `DataManagementService.import_edon2_csv`. Brukes for manuell/planlagt import. |
| **`backend/scripts/migrer_og_import_edon2_avdeling.py`** | Hjelpescript: kjører først `alembic upgrade head` (migrering), deretter e-don2-import slik at matchende eiendommer får satt avdelingsfeltene. |
| **`backend/app/api/v1/import_api.py`** | API-endepunkt for e-don2-import (f.eks. ved fil-opplasting). |

**Datakilde som leses:** Innhold fra filer som `backend/e-don2.txt`, `backend/e-dom.txt` (eller tilsvarende navn). Disse forventes å ha kolonnene **Enhetskorttype** og **Enhetstype (Utledet)** (evt. med normalisering via `alt_names` i `data_management.py`).

### 4.2 Frontend – visning

| Fil | Rolle |
|-----|--------|
| **`frontend/lib/types.ts`** | TypeScript-interface `Property`: feltene `unit_id_erp`, `unit_short_type`, `unit_type_derived` (samt `ownership_type`, `closed_at`, `legal_basis` for konsistens). |
| **`frontend/app/properties/[id]/page.tsx`** | Eiendomsdetaljsiden: viser **Enhet ID (ERP)**, **Enhetstype** (`unit_short_type`) og **Formål (utledet)** (`unit_type_derived`) med tooltips, i samme blokk som Eierskap og Status. |

API-ene **`GET /properties/{id}`** og **`GET /properties/{id}/detail-view`** returnerer allerede disse feltene fra backend; frontend bruker dem bare til visning og trenger ingen ekstra endepunkter.

### 4.3 Dokumentasjon og referanse

| Fil | Rolle |
|-----|--------|
| **`docs/MINNEFIL_KOSTNADSFORDELING_AVDELING.md`** | § 3, § 27–28: forklaring av e-don2, birk_og_plasser, Enhetskorttype, Enhetstype (Utledet), og at import nå lagrer `unit_short_type` og `unit_type_derived`. |
| **`docs/EIENDOMMER_AVDELINGER_DATA_OG_FILER.md`** | Denne filen – detaljert oversikt over data og filer. |

---

## 5. Kort flyt

```
e-don2.txt / e-dom.txt (backend/)
         │
         ▼
import_edon2_csv (data_management.py)
         │
         ├── Leser TSV/CSV, normaliserer kolonnenavn (Enhetskorttype, Enhetstype (Utledet))
         ├── Matcher hver rad mot eiendom (Lokasjonskode, EnhetID, adresse, fuzzy)
         └── Oppdaterer Property: unit_id_erp, unit_short_type, unit_type_derived, ...
         │
         ▼
properties (DB) med unit_short_type, unit_type_derived
         │
         ▼
GET /properties/{id} og GET /properties/{id}/detail-view
         │
         ▼
Frontend: types.ts (Property), properties/[id]/page.tsx (visning Enhetstype + Formål utledet)
```

---

## 6. Kjøre migrering og import (fylle data)

For å sikre at kolonnene finnes og at eiendommer får fylt avdelingsfeltene:

1. **Migrering** (én gang):  
   Fra `backend/` med `DATABASE_URL` satt:  
   `alembic upgrade head`

2. **Import**:  
   - Enten: `python app/scripts/import_edon2_data.py` fra `backend/` (leser e-don2.txt, e-dom.txt m.m. i backend/).  
   - Eller: `python scripts/migrer_og_import_edon2_avdeling.py` fra `backend/` (kjører migrering + import).  
   - Eller: bruk import-API med opplasting av e-don2/e-dom-fil.

Etter vellykket import har matchende eiendommer satt **Enhetstype** og **Formål (utledet)** på eiendomsdetaljsiden.
