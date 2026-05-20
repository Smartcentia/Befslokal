# Oversikt bygg og eiendom – GK og Budsjetterte (Ark1)

**Fil:** `Oversikt bygg og eiendom - GK og Budsjetterte(Ark1).csv`  
(typisk i `~/Downloads/`)

## Struktur

- **Separator:** semikolon (`;`) eller komma (`,`)
- **Første rad:** ekstra header med blant annet «Kontraktforpliktelser», «Beskrivelse av egnethet»
- **Andre rad (kolonnenavn):**  
  `Lokalisering;Avtalenavn;Region;Adresselinje 1;Postnr;Poststed;Startdato;Sluttdato;Utleier;Status;Lok: Område;Kommunenavn;Kontraktsleie;Indre vedlikehold;Felleskostnader;Brukeravhengige driftskostnader;Varighet;...;Institusjonstype /Type lokasjon;Målgruppe;Antall G/K - plasser;Antall budsjetterte plasser;Hjemmel §;Egnethet lokalisering;Egnethet bygg;Priortert viderført /utviklet;År for videreutvikling;Kostnader til videreutvikling`
- **Ca. 210–225 datarader**

### Oppdatert CSV-format (nyere versjoner)

Nyere eksporter kan ha:
- **Komma** som separator (i stedet for semikolon)
- **US-datoformat** (M/D/YYYY) i stedet for DD.MM.YYYY
- **Egnethet lokalisering** og **Egnethet bygg** fylt med tall 1–4 (fargekode: 1=rød, 2=oransje, 3=gul, 4=grønn)

## Viktige kolonner

| Kolonne | Betydning | Mulig kobling til BEFS |
|--------|-----------|-------------------------|
| **Lokalisering** | Kode + navn (f.eks. `4818 - Gulset`, `3506 - KASA Morvik`) | Kan brukes til matching mot eiendom (navn/adresse); evt. `lokalisering_id` hvis koden er numerisk |
| **Avtalenavn** | Kontraktens/avtalens navn | `contract` beskrivelse / tittel |
| **Region** | Sør, Øst, Vest, Nord, Midt | `properties.region` |
| **Adresselinje 1, Postnr, Poststed** | Adresse | `properties.address`, `postal_code`, `city` |
| **Startdato, Sluttdato** | Kontraktens periode | `contracts.start_date`, `end_date` |
| **Utleier** | Utleier (Statsbygg, kommuner, private) | Parti/utleier |
| **Status** | Aktiv, etc. | `contracts.status` |
| **Kontraktsleie, Indre vedlikehold, Felleskostnader** | Økonomi | Kontraktsbeløp / vedlikehold |
| **Institusjonstype / Type lokasjon** | Familievernkontor, Formålsbygg, Kontor | Type bruk / `usage` |
| **Målgruppe** | FVK, BFS, Kontor, Akutt, Behandling høy, Omsorg, etc. | Kategorisering |
| **Antall G/K - plasser, Antall budsjetterte plasser** | GK-plasser og budsjetterte plasser | Kapasitet |
| **Hjemmel §** | Lovparagrafer (barnevern, omsorg, etc.) | Juridisk grunnlag |

## Forskjell fra Birk-institusjoner-CSV

- **Birk (Institusjoner … Formålsbygg):** Enhetsregister-hierarki – **EnhetID** og **TilhørighetEnhetID** (enhet ↔ forelder). Egnet til å sette `parent_unit_id_erp` / `unit_id_erp` på *eiendommer*.
- **Oversikt bygg og eiendom (denne filen):** **Kontrakts-/leieoversikt** per *lokalisering* – avtaler, adresser, utleier, beløp, GK/budsjett. Ingen EnhetID/TilhørighetEnhetID.

## Kobling til BEFS

- **Eiendom:** Multi-pass matching (prioritetsrekkefølge):
  1. `lokalisering_id` – parse kode fra «XXXX - Navn» (f.eks. 4711)
  2. `navn_contains` – parse navn fra Lokalisering, match mot `properties.name` (f.eks. «Furuly» matcher «NyeFuruly»)
  3. `adresse_exact` – Adresselinje 1 + Postnr + Poststed, normalisert
  4. `adresse_heuristic` – gata→gt, veien→vg (én kandidat)
  5. `adresse_fuzzy` – SequenceMatcher ≥ 0.85
  6. `navn_fuzzy` – SequenceMatcher ≥ 0.80
- **Kontrakter:** Hver rad kan representere eller supplere en kontrakt (avtale) knyttet til en eiendom/enhet; feltene Startdato/Sluttdato, Kontraktsleie, Utleier, Status kan brukes ved import/synk av kontrakter.
- **GK/budsjett:** «Antall G/K - plasser» og «Antall budsjetterte plasser» kan lagres som egne felter eller i `external_data` på eiendom/kontrakt dersom BEFS skal vise dette.

## Eksempler fra filen

- `4818 - Gulset` → Gulsetringen 313, SKIEN; Formålsbygg, BFS; Kontraktsleie 3 593 500.
- `3506 - KASA Morvik` → Lokketomarka 24, MJØLKERÅEN; Formålsbygg, Omsorg; 3 GK-plasser, 3 budsjetterte.
- `5914 - Energiveien 14, 2069 Jessheim` → Familievernkontoret; leie til 31.12.2029.

Denne filen er dermed komplementær til Birk-CSV: Birk gir **institusjons-/enhetshierarki** (parent–child), mens denne gir **avtaler og bygg/lokalisering** med økonomi og GK/budsjett.

## Import-script

`backend/scripts/import_oversikt_bygg_eiendom_csv.py` importerer fra CSV til BEFS via Supabase REST API eller DATABASE_URL.

```bash
cd backend
# Med DATABASE_URL (anbefalt)
railway run python3 scripts/import_oversikt_bygg_eiendom_csv.py --use-db [--csv PATH] [--dry-run] [--report]

# Med Supabase
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/import_oversikt_bygg_eiendom_csv.py [--csv PATH] [--dry-run]
```

- Støtter både semikolon og komma, samt DD.MM.YYYY og M/D/YYYY
- **Matching:** Multi-pass (lokalisering_id → navn_contains → adresse_exact → adresse_heuristic → adresse_fuzzy → navn_fuzzy)
- **--report:** Vis match-rapport uten import (kun med --use-db)
- Oppdaterer: properties (affiliation, approved_places, budgeted_places, legal_basis, external_data), contracts (amount, external_data, party_id)

---

## Felt-for-felt: CSV vs database

### CSV-kolonner (31 felter)

| # | CSV-felt | DB-tabell | DB-felt | Match |
|---|----------|-----------|---------|-------|
| 1 | Lokalisering | properties | lokalisering_id (parse kode fra "XXXX - Navn") | ✅ |
| 2 | Avtalenavn | contracts / units | external_data / purpose | ✅ |
| 3 | Region | properties | region | ✅ |
| 4 | Adresselinje 1 | properties | address | ✅ |
| 5 | Postnr | properties | postal_code | ✅ |
| 6 | Poststed | properties | city | ✅ |
| 7 | Startdato | contracts | start_date | ✅ |
| 8 | Sluttdato | contracts | end_date | ✅ |
| 9 | Utleier | parties | name | ✅ |
| 10 | Status | contracts | status | ✅ |
| 11 | Lok: Område | properties | lok_omrade | ✅ |
| 12 | Kommunenavn | properties | municipality | ✅ |
| 13 | Kontraktsleie | contracts | amount.amount_per_year | ✅ |
| 14 | Indre vedlikehold | contracts | external_data | ✅ |
| 15 | Felleskostnader | contracts | external_data | ✅ |
| 16 | Brukeravhengige driftskostnader | contracts | external_data | ✅ |
| 17 | Varighet | contracts | periods / external_data | ✅ |
| 18 | Adgang til forlengelse og vilkår | contracts | has_option / external_data | ✅ |
| 19 | Årlig prisjusteringsfaktaktor | contracts | regulation_type / external_data | ✅ |
| 20 | Merknad | contracts | external_data | ✅ |
| 21 | Region (duplikat) | — | — | ⚠️ Samme som #3 |
| 22 | Institusjonstype / Type lokasjon | properties | usage | ✅ |
| 23 | Målgruppe | properties | affiliation / external_data | ✅ |
| 24 | Antall G/K - plasser | properties | approved_places | ✅ |
| 25 | Antall budsjetterte plasser | properties | budgeted_places | ✅ |
| 26 | Hjemmel § | properties | legal_basis | ✅ |
| 27 | Egnethet lokalisering | properties | egnethet_lokalisering | ✅ |
| 28 | Egnethet bygg | properties | egnethet_bygg | ✅ |
| 29 | Priortert viderført /utviklet | properties | prioritert_videroforing | ✅ |
| 30 | År for videreutvikling | properties | ar_videreutvikling | ✅ |
| 31 | Kostnader til videreutvikling | properties | kostnader_videreutvikling | ✅ |

### Oppsummering

- **Alle 31 CSV-felter** har en tilsvarende plass i databasen.
- **Direkte mapping:** 18 felter mappes til egne kolonner (properties, contracts, parties).
- **Via external_data:** 12 felter kan lagres i `external_data` (JSONB) på property eller contract.
- **Duplikat:** Region forekommer to ganger (kol. 3 og 21); bruk én av dem.

### Felter som mangler i databasen (som egne kolonner)

Alle felter er nå enten egne kolonner eller lagret i `external_data`. Nye egne kolonner lagt til (2026-05-09):

- `egnethet_lokalisering`, `egnethet_bygg` — egne VARCHAR-kolonner på `properties`
- `prioritert_videroforing`, `ar_videreutvikling`, `kostnader_videreutvikling` — egne kolonner på `properties`
- `lok_omrade`, `lok_distrikt`, `fylke` — egne VARCHAR-kolonner på `properties`
- `leased_area_kvm` — eget NUMERIC-felt for leid areal
- `elements_id` — eget VARCHAR-felt for Elements saksnummer
- `utleier_kategori` — eget SMALLINT-felt (1=privat, 2=offentlig)
- `contract_rent_nok`, `contract_maint_nok`, `contract_common_nok`, `contract_user_ops_nok` — egne NUMERIC-felt for kontraktsbeløp
- `extension_terms`, `price_adj_clause` — egne VARCHAR-felt

Følgende brukes fortsatt via `external_data`:
- `regulation_type` (Årlig prisjusteringsfaktaktor) – finnes på Property, ikke Contract
- `contract_description` / `title` – Avtalenavn i `contracts.external_data` eller `units.purpose`

> **Merk:** `import_oversikt_bygg_eiendom_csv.py` ble opprinnelig skrevet til å lagre egnethet- og videreutvikling-felt i `external_data`. Scriptet bør oppdateres til å bruke de nye dedikerte kolonnene.
