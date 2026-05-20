# Finansiell Oversikt – CSV vs database vs UI

Sammenligning av kontraktsdata fra CSV-filen «Oversikt bygg og eiendom - GK og Budsjetterte» mot databasen og Finansiell Oversikt i BEFS.

## Feltoversikt

| CSV-felt | Betydning | DB-tabell | DB-felt | I UI i dag? |
|----------|-----------|-----------|---------|-------------|
| **Lokalisering** | Unikt navn på eiendom (f.eks. "4818 - Gulset") | properties | `lokalisering_id` (kode) + `name` | Ja (ENHET i tabell) |
| **Avtalenavn** | Kontraktens navn | contracts / units | `external_data.contract_name` / `units.purpose` | Delvis (via kontraktlenke) |
| **Region** | Midt, Sør, Øst, Vest, Nord | properties | `region` | Ja |
| **Adresselinje 1** | Gateadresse | properties | `address` | Ja |
| **Kontraktsleie** | Årlig husleie | contracts | `amount.amount_per_year` | ✅ Ja – som «Husleie (Årsleie)» |
| **Indre vedlikehold** | Indre vedlikehold kr/år | contracts | `external_data.internal_maintenance_cost` | ❌ Nei |
| **Felleskostnader** | Felleskostnader kr/år | contracts | `external_data.common_costs` | ❌ Nei |
| **Brukeravhengige driftskostnader** | Brukeravhengige driftskostnader kr/år | contracts | `external_data.user_dependent_costs` | ❌ Nei |
| **Adgang til forlengelse og vilkår** | F.eks. "JA, må vasle utleier om forlengelse min 12 mnd før utløp" | contracts | `has_option` + `external_data.extension_terms` | ❌ Nei |
| **Årlig prisjusteringsfaktaktor** | F.eks. "100% av KPI på leie" | properties / contracts | `regulation_type` / `external_data.regulation_type` | ❌ Nei |

## Detaljert mapping

### 1. Husleie = Kontraktsleie ✅

- **CSV:** `Kontraktsleie`
- **DB:** `contracts.amount.amount_per_year`
- **UI:** «Husleie (Årsleie)» – sum av aktive kontrakter
- **Status:** Allerede implementert. Kontraktsleie fra CSV skal importeres hit.

### 2. Indre vedlikehold ❌

- **CSV:** `Indre vedlikehold`
- **DB:** 
  - `contracts.external_data.internal_maintenance_cost` (per kontrakt)
  - `property_annual_costs.internal_maintenance` (per år – tabell tømt)
- **UI:** Ikke vist i Finansiell Oversikt
- **Anbefaling:** Legg til eget felt i et nytt «Kontraktskostnader»-kort under Finansiell Oversikt. Ved import fra CSV: skriv til `contracts.external_data.internal_maintenance_cost`.

### 3. Felleskostnader ❌

- **CSV:** `Felleskostnader`
- **DB:** 
  - `contracts.external_data.common_costs`
  - `property_annual_costs.common_costs`
- **UI:** Ikke vist
- **Anbefaling:** Samme som indre vedlikehold – vis i nytt kort, importer til `contracts.external_data.common_costs`.

### 4. Brukeravhengige driftskostnader ❌

- **CSV:** `Brukeravhengige driftskostnader`
- **DB:** `contracts.external_data.user_dependent_costs`
- **UI:** Ikke vist
- **Anbefaling:** Vis i samme «Kontraktskostnader»-kort, importer til `external_data.user_dependent_costs`.

### 5. Adgang til forlengelse og vilkår ❌

- **CSV:** `Adgang til forlengelse og vilkår`
- **DB:** 
  - `contracts.has_option` (bool)
  - `contracts.external_data.extension_terms` (fri tekst, f.eks. "JA, må vasle utleier om forlengelse min 12 mnd før utløp")
- **UI:** Ikke vist i Finansiell Oversikt
- **Anbefaling:** Ny seksjon under Finansiell Oversikt: «Kontraktsvilkår» med Adgang til forlengelse og Årlig prisjusteringsfaktor.

### 6. Årlig prisjusteringsfaktaktor (KPI) ❌

- **CSV:** `Årlig prisjusteringsfaktaktor`
- **DB:** 
  - `properties.regulation_type`
  - `contracts.external_data.regulation_type` (per kontrakt)
- **UI:** Ikke vist
- **Anbefaling:** Vis sammen med forlengelse i «Kontraktsvilkår».

## Prioritet for implementering

1. **Import fra CSV** – Skriv Kontraktsleie, Indre vedlikehold, Felleskostnader, Brukeravhengige driftskostnader, Adgang til forlengelse, Årlig prisjusteringsfaktaktor til riktige DB-felter.
2. **Nytt kort: Kontraktskostnader** – Vis Indre vedlikehold, Felleskostnader, Brukeravhengige driftskostnader (fra kontrakter knyttet til eiendom).
3. **Nytt kort: Kontraktsvilkår** – Vis Adgang til forlengelse og vilkår, Årlig prisjusteringsfaktaktor (KPI).

## Erstatningslogikk

> «alt skal inn og eventuelt erstattes dersom det er data i feltene i finansiell oversikt»

- **Kontraktsleie:** Alltid fra kontrakt (`amount.amount_per_year`). GL «Faktisk husleie» er separat og viser bokført leie – behold begge.
- **Indre vedlikehold, Felleskostnader, Brukeravhengige:** Ved import fra CSV – overskriv `external_data` på kontrakten. Disse erstatter ikke GL «Bokførte kostnader», som kommer fra regnskap.
- **Adgang til forlengelse, KPI:** Kun fra kontrakt – ingen konflikt med GL.

## Database-sjekk

| Felt | contracts | property_annual_costs | properties |
|------|-----------|----------------------|------------|
| Kontraktsleie | `amount.amount_per_year` | `kpi_adjusted_rent` | — |
| Indre vedlikehold | `external_data.internal_maintenance_cost` | `internal_maintenance` | — |
| Felleskostnader | `external_data.common_costs` | `common_costs` | — |
| Brukeravhengige | `external_data.user_dependent_costs` | — | — |
| Forlengelse | `has_option`, `external_data.extension_terms` | — | — |
| KPI-faktor | `external_data.regulation_type` | — | `regulation_type` |

Alle felter finnes i databasen. Mangler kun i UI og i import fra «Oversikt bygg og eiendom»-CSV.

---

## Egnethet – tallkoding (1–4)

| Tall | Farge   | Betydning       |
|------|---------|-----------------|
| 1    | Rød     | Lavest egnethet |
| 2    | Oransje |                 |
| 3    | Gul     |                 |
| 4    | Grønn   | Best egnethet   |

Lagres i `properties.external_data` som `egnethet_lokalisering` og `egnethet_bygg` (integer 1–4).

---

## Property_husleie_csv – Total kost fra Innkjøpsanalyse (2025)

| Felt | Betydning | Kilde |
|------|-----------|-------|
| `property_id` | Eiendom | |
| `year` | År (2025) | |
| `region` | Midt-Norge, Nord, Sør, Vest, Øst, Bufdir | CSV-kolonner |
| `amount` | Sum Total kost | Aggregert fra alle kategorier under «Leie av lokaler og tilknyttede utgifter» |
| `source` | `innkjøpsanalyse_2025` | |

**Total kost** = hele blokken «Leie av lokaler og tilknyttede utgifter» (husleie + fellesutgifter, strøm, renhold, reparasjon m.m.). Import script: `backend/scripts/import_innkjøpsanalyse_husleie.py`. Genererer `backend/data/total_kost_per_region_{year}.json` for regionvisning i UI.

## Implementert (2025)

- **Import-script:** `backend/scripts/import_oversikt_bygg_eiendom_csv.py`
- **Import-script Total kost:** `backend/scripts/import_innkjøpsanalyse_husleie.py` – importerer «Leie av lokaler og tilknyttede utgifter» til `property_husleie_csv` og `backend/data/total_kost_per_region_{year}.json`
- **UI-kort:** «Kontrakts- og egnethetsdata» under Finansiell Oversikt på eiendomsdetalj
- **Felter i kortet:** Målgruppe, Antall G/K - plasser, Antall budsjetterte plasser, Hjemmel §, Utleier, Årlig prisjusteringsfaktaktor, Egnethet lokalisering/bygg (fargekodet), Priortert viderført /utviklet, År for videreutvikling, Kostnader til videreutvikling (viser «Kommer» når tom)
