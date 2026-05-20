# Datakilder: eiendom, kontrakt og finans (BEFS)

Dette dokumentet definerer **parallelle sannheter** i systemet slik at UI, rapporter og revisjon ikke blander begreper.

| Begrep | Primær kilde | Typisk bruk |
|--------|----------------|-------------|
| **Kontraktsfestet leie** | `contracts.amount` → `amount_per_year` / `total_per_year` (JSON) | Avtale, budsjett, forventet kostnad, «Finansiell analyse» (kontrakt-lag) |
| **Avtalefestet leie (direkte kolonne)** | `properties.contract_rent_nok` | Snap-shot av avtalefestet husleie fra Eiendomsportefølje-CSV. ~181 eiendommer, ~319 MNOK. Overskrives aldri av GL-data. |
| **Faktisk husleie GL 2025 (direkte kolonne)** | `properties.gl_rent_2025` | Faktisk bokført husleie 2025 fra Agresso (srs_kategori='Lokaler'). ~145 eiendommer, ~430 MNOK. Overskrives aldri av kontraktsdata. |
| **Faktisk husleie (bokført, løpende)** | `gl_transactions` der `konto_navn` klassifiseres som leie via `is_lease_account()` | Regnskap, avvik mot kontrakt, faktisk kostnad |
| **Drift / øvrige kostnader (bokført)** | `gl_transactions` (sum minus husleie-posteringer), ev. `srs_kategori` | Kostnadsbilde fra Agresso |
| **Manuelle utgifter** | `properties.external_data.financials.manual_expenses` | Utfylling der GL ikke brukes eller som supplement |
| **Årlige kostnader (CSV-import)** | `property_annual_costs` (f.eks. KPI-justert leie, felleskost, energi) | Eiendomsportal / importerte budsjetter |

> **Arkitekturpoeng:** `contract_rent_nok` og `gl_rent_2025` representerer to uavhengige sannheter. En typisk differanse er ~111 MNOK (430 − 319). Dette skyldes omposteringer, nye kontrakter i 2025, og at GL dekker færre eiendommer enn kontraktsdata. Presenter alltid begge tall med kildeangivelse.

## Viktige koblingsnøkler (GL → eiendom)

- **Direkte:** `gl_transactions.property_id`
- **Via koststed:** `gl_transactions.dim1_kode` sammenholdt med `properties.department_code` eller `properties.koststed_kode`
- **Orphan-rader:** `property_id IS NULL` – matches mot `properties.unit_id_erp` (normalisert Dim1), se `gl-financial-bulk` og `financial-summary` i API.

## Hva «mangler husleie» kan bety

| Situasjon | Betydning |
|-----------|-----------|
| Admin «Finansiell analyse» viser mangler husleie | Ofte: **ingen kontraktsbeløp** (`amount_per_year`), ikke nødvendigvis manglende Agresso-poster |
| Faktisk husleie i regnskap | Se GL / `financial-summary` – kan være tilstede selv om kontraktsdata mangler |
| Begge mangler | Datahull som bør prioriteres (koblingsnøkkel + import) |

## Institusjonsnivå uten `units` / kontrakter i DB

Mange eiendommer har **regnskap på institusjon** (GL koblet via koststed) uten at det finnes rader i `units` eller aktive `contracts` i BEFS. Revisjonen bruker da merknadene `no_units_institution_level_gl` og `no_contracts_institution_level_gl` i stedet for harde `no_units` / `no_active_contracts`, og gir **delkreditt i score** når GL finnes.

## Referanseimplementasjon

- GL-klassifisering: [backend/app/models/gl_constants.py](backend/app/models/gl_constants.py)
- Bulk GL per eiendom: [backend/app/domains/core/routers/properties.py](backend/app/domains/core/routers/properties.py) (`gl-financial-bulk`, `financial-summary`)
- Helhetlig revisjon (rapport): [backend/scripts/audit_properties_full.py](backend/scripts/audit_properties_full.py)

## Eiendomsside (UI) og datakilder

Feltmatrise (hovedfelt) vedlikeholdes i [backend/app/services/financials/property_ui_surface_audit.py](backend/app/services/financials/property_ui_surface_audit.py) og speiles i `enrich_property_data` + `frontend/app/properties/[id]/page.tsx`.

Revisjon av **finansår vs GL** (risiko for tomme kort når siste regnskapsår er før inneværende år): kjør `audit_properties_full.py --ui-surface` → `backend/data/property_ui_surface_gaps.csv`.
