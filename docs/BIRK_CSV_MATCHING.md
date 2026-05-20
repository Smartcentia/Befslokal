# Birk CSV – Institusjoner i og utenfor staten (Formålsbygg)

**Fil:** `Institusjoner  i og utenfor staten - Formålsbygg(ERA-01 Enhetsregister (Birk) Fl).csv`  
(typisk i `~/Downloads/`)

## Struktur

- **Separator:** semikolon (`;`)
- **Første rad:** tom/header
- **Header (rad 2):**  
  `Region;Tilhørighet2;TilhørighetEnhetID;Tilhørighet;EnhetID;Enhetsnavn;Enhetskorttype;Enhetstype (Utledet);Antall G/K - plasser;Hjemler;Eierskapenhet;Lokasjonskode;Fylke;Kommune;Adresse;Postnummer;Poststed`

## Viktige kolonner for parent-matching

| Kolonne | Betydning | Tilsvarer i BEFS DB |
|--------|-----------|----------------------|
| **EnhetID** | Enhetens ID i Enhetsregisteret (Birk) | `properties.unit_id_erp` |
| **TilhørighetEnhetID** | Forelderenhetens EnhetID | `properties.parent_unit_id_erp` |
| **Enhetsnavn** | Enhetens navn | `properties.name` |
| **Enhetskorttype** | Avdeling, Barnevernsinstitusjon, osv. | `properties.unit_short_type` |
| **Tilhørighet** | Forelderenhetens navn | tilsvarer affiliation/forelder-navn |
| **Region** | Region | `properties.region` |
| **Adresse, Postnummer, Poststed, Fylke, Kommune** | Adresseinfo | `properties.address`, `postal_code`, `city` |

## Kobling til BEFS

- I BEFS brukes **strategi 1** for parent: eiendom med `parent_unit_id_erp` = X får `parent_property_id` = den eiendommen som har `unit_id_erp` = X.
- Birk-CSV inneholder **nøyaktig denne koblingen**: hver rad har `EnhetID` (enhet) og `TilhørighetEnhetID` (forelder).
- **Konklusjon:** Hvis vi for hver eiendom i DB som har `unit_id_erp` finner raden i CSV der `EnhetID` = `unit_id_erp`, og setter `parent_unit_id_erp` = `TilhørighetEnhetID` fra den raden (når den er ikke-tom), vil strategi 1 begynne å treffe for alle der forelder-eiendom også finnes i DB (med `unit_id_erp` = TilhørighetEnhetID).

## Forslag til oppdatering

1. **Import/oppdatering fra Birk-CSV:**  
   For hver rad i CSV:  
   - Finn eventuell eiendom i BEFS der `unit_id_erp` = `EnhetID` (evt. som string).  
   - Hvis `TilhørighetEnhetID` er satt: oppdater `parent_unit_id_erp` = `TilhørighetEnhetID`.  
   - Evt. oppdater også `unit_short_type` fra `Enhetskorttype`, `region` fra `Region`, osv.

2. **Forelder må finnes:**  
   For at `parent_property_id` skal vises i API, må det finnes en eiendom i DB med `unit_id_erp` = `TilhørighetEnhetID`. I Birk-CSV er foreldre ofte egne rader (f.eks. «adm»-enheter med egen `EnhetID`). Så enten:  
   - disse er allerede importert som eiendommer, eller  
   - vi må importere manglende forelder-rader fra CSV som nye eiendommer (eller sikre at de finnes fra annen kilde).

3. **Om filen:**  
   Ca. 588 datarader (590 linjer minus header). Dekker institusjoner med formålsbygg i Enhetsregisteret (Birk), inkl. statlige og private, med full hierarki-informasjon (TilhørighetEnhetID).

## Script: oppdater parent fra Birk CSV

Scriptet `backend/scripts/oppdater_parent_erp_fra_birk_csv.py` bruker **Supabase REST API** (ingen direkte DB-tilkobling). Det leser Birk-CSV og oppdaterer `parent_unit_id_erp` (og valgfritt `unit_short_type`, `region`) på eiendommer som har `unit_id_erp` som finnes i CSV.

**Miljøvariabler:** `SUPABASE_URL` (valgfri), `SUPABASE_SERVICE_ROLE_KEY` eller `SUPABASE_SERVICE_KEY` (påkrevd for REST API).

**Kjør fra backend-mappen:**

```bash
cd backend

# Først dry-run (ingen endringer lagres)
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/oppdater_parent_erp_fra_birk_csv.py --dry-run

# Med oppdatering av unit_short_type og region fra CSV
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/oppdater_parent_erp_fra_birk_csv.py --dry-run --oppdater-felter

# Faktisk oppdatering
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/oppdater_parent_erp_fra_birk_csv.py
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/oppdater_parent_erp_fra_birk_csv.py --oppdater-felter
```

Hvis `SUPABASE_URL` og `SUPABASE_SERVICE_ROLE_KEY` står i `backend/.env`, trenger du ikke å sette dem på kommandolinjen.

`--csv` har default `~/Downloads/Institusjoner  i og utenfor staten - Formålsbygg(ERA-01 Enhetsregister (Birk) Fl).csv`. Overstyr med `--csv /path/to/fil.csv`.

**Etter kjøring:** Eiendommer som har forelder i DB med riktig `unit_id_erp` får `parent_property_id` i API (get_properties / sub-units).

---

## Oppslag for de som mangler (Brønnøysund)

For eiendommer som fortsatt mangler forelder (f.eks. ikke i Birk-CSV eller uten `unit_id_erp`), kan du bruke **Brønnøysund Enhetsregisteret** (åpent API): underenheter har feltet `overordnetEnhet` (organisasjonsnummer til overordnet enhet).

Scriptet `backend/scripts/slaa_opp_manglende_parent_brreg.py`:

1. Henter eiendommer som har `org_number` men mangler `parent_unit_id_erp`.
2. Kaller `GET https://data.brreg.no/enhetsregisteret/api/underenheter/{orgnr}` for hver.
3. Hvis svaret inneholder `overordnetEnhet`, sjekkes det om vi har en eiendom i DB med `org_number` = det nummeret.
4. Skriver ut treff og kan skrive CSV med `--csv fil.csv`.

Dette gir kun treff der eiendommens `org_number` er en **underenhet** i Enhetsregisteret. Forelder-eiendom må ha samme `org_number` som overordnet enhet i Brønnøysund for at vi skal finne den i DB. Ingen API-nøkkel trengs for Brønnøysund.

```bash
cd backend
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/slaa_opp_manglende_parent_brreg.py
SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/slaa_opp_manglende_parent_brreg.py --csv treff_manglende.csv
```
