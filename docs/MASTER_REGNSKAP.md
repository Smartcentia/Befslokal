# Master regnskap – datastruktur og visning

## Formål

Master regnskap er sannhetskilden for eiendoms- og kostnadsdata i BEFS. Det samler:

- **Eiendommer** (properties)
- **Avdelinger** (units)
- **Kontrakter** (contracts)
- **Leietakere** (parties)
- **Husleie** (fra kontrakter og regnskap)
- **Løpende kostnader** (fra GL 2020–2025)
- **Ekstern statistikk** (fra SSB)

## Datakilder

| Kilde | Tabell/API | Beskrivelse |
|-------|------------|-------------|
| Eiendommer | `properties` | Masterdata fra e-don2, Eie1212, Oversikt bygg og eiendom |
| Avdelinger | `units` | Organisatoriske enheter knyttet til eiendommer |
| Kontrakter | `contracts` | Leieavtaler med party (utleier), amount (leie) |
| Leietakere | `parties` | Utleiere/hjemmelshavere |
| **GL 2020–2025** | `gl_transactions` | Linjespesifikke transaksjoner fra Kontant-CSV (Xledger/Visma). 136 055 rader. |
| **Aggregerte kostnader** | `property_husleie_csv` | Total kost (husleie + løpende) fra Innkjøpsanalyse |
| Årlige kostnader | `property_annual_costs` | Nedbrytning per kategori (Eiendomsportefølje) |
| **Budsjett 2026** | `budget` | GL-basert kategori-estimat. 605 MNOK. |
| **Ekstern statistikk** | SSB PxWeb API | KPI, byggekostnadsindeks, leieprisindeks m.m. |

## Kostnadsvolum per år (GL)

| År | Totale kostnader |
|----|---:|
| 2020 | 415 800 000 NOK |
| 2021 | 452 300 000 NOK |
| 2022 | 490 100 000 NOK |
| 2023 | 518 600 000 NOK |
| 2024 | 531 737 000 NOK |
| 2025 | 567 522 501 NOK |
| **2026 (budsjett)** | **604 963 648 NOK** |

Kilde: `gl_transactions` for 2020–2025, `budget`-tabell for 2026.
Vises i **«Master regnskap – datakilder»**-kortet på /financials.

## To typer kostnadsvisning

### 1. Detaljerte kostnader 2020–2025

**Kilde:** `gl_transactions` (importert via `import_kontant_2024_2025.py` og lignende)

- Linjespesifikke transaksjoner per konto (`account_name`)
- Dekker 2020–2025 (136 055 rader totalt)
- Vises som **eget kort** på eiendomssiden og Finansiell oversikt
- Inneholder: Leie lokaler, Fellesutgifter, Strøm, Renhold, Reparasjon, Vaktmester m.m.

**API:** `GET /properties/{id}/financial-summary?year=2024` og `?year=2025`

### 2. Aggregerte kostnader

**Kilde:** `property_husleie_csv` (importert via `import_innkjøpsanalyse_husleie.py`)

- **Total kost** = hele blokken «Leie av lokaler og tilknyttede utgifter»
- Inkluderer husleie + løpende utgifter (fellesutgifter, strøm, renhold, reparasjon m.m.)
- Vises som **eget kort** på eiendomssiden og Finansiell oversikt

**API:** `GET /properties/innkjoepsanalyse-husleie?year=2025` → `by_property[property_id].aggregert`

## Husleie-definisjon

Fra [AVSTEM_HUSLEIE_2025_RAPPORT.md](AVSTEM_HUSLEIE_2025_RAPPORT.md):

- **Husleie** = kun: «Leie lokaler andre utleiere» + «Leie lokaler fra Statsbygg»
- **Ikke** husleie: Leie parkeringsplass, Fellesutgifter, Strøm, Renhold, Reparasjon, Annen kostnad lokaler

## Budsjett 2026 – metodikk

Budsjett 2026 er generert med **kategori-basert GL-estimering** fra `budget_2026_kategori.py`:

- **Husleie** (364 MNOK faktisk 2025) × 1,047 = **381 MNOK**
- **Drift** (203 MNOK faktisk 2025) × 1,100 = **223 MNOK**
- **Total 2026: 605 MNOK** (+6,6 % fra 2025)

84 % av GL-kostnadene er bokført på sentrale Koststed-koder og fordeles proporsjonalt
til 74 kjente eiendommer. Se [BUDSJETT_2026_ESTIMERING.md](BUDSJETT_2026_ESTIMERING.md) for detaljer.

## SSB – ekstern statistikk

BEFS integrerer med **Statistisk sentralbyrå (SSB) PxWeb API v2** for å hente
offisiell norsk statistikk. Ingen API-nøkkel kreves.

**Tilgjengelig via KI-Kollega:**
- KPI (konsumprisindeks) og inflasjon
- Byggekostnadsindeks
- Leieprisindeks for næringslokaler
- Andre relevante tabeller

**Eksempelspørsmål til KI-Kollega:**
- «Hva er KPI nå?»
- «Sammenlign våre kostnader med KPI de siste 5 årene»
- «Hva er den offisielle byggekostnadsindeksen?»

**Direkte SSB-side:** `/ssb` i applikasjonen (DATA & STATISTIKK i sidebaren)

**API-endepunkter:**
- `GET /api/v1/ssb/tables?q=<søkeord>` – søk i SSB-tabeller
- `GET /api/v1/ssb/table/{table_id}?variables=...` – hent tabelldata

## UI-kort

| Kort | Plassering | Innhold |
|------|------------|---------|
| **Master regnskap – datakilder** | /financials | GL-totaler per år (2020–2025) + 2026 budsjett |
| **Detaljerte kostnader** | Eiendomsside, Finansiell oversikt | GL-transaksjoner per konto for hvert år |
| **Aggregerte kostnader** | Eiendomsside, Finansiell oversikt | Total kost fra Innkjøpsanalyse (husleie + løpende) |
| Kostnader per år | Eiendomsside | property_annual_costs (Eiendomsportefølje) |
| **Budsjett 2026** | Eiendomsside | 605 MNOK GL-basert, fordelt per eiendom |
| Kostnadsanalyse | Eiendomsside | Forhold kostnader/husleie |

## Importrekkefølge

1. `import_master_data.py` – eiendommer, kontrakter fra Eie1212
2. `import_oversikt_bygg_eiendom_csv.py` – supplering av eiendomsdata
3. `import_kontant_2024_2025.py` – detaljerte GL-transaksjoner 2024–2025
4. `import_innkjøpsanalyse_husleie.py` – aggregerte kostnader (Total kost)
5. `budget_2026_kategori.py` – generer budsjett 2026

## Dokumenter og KI-Kollega

### text_content (dokumenter)

Tabellen `text_content` inneholder chunked dokumenter (rutiner, krav, instrukser) som KI-Kollega bruker via verktøyet `search_documents`.

**Hvis databasen tømmes** (f.eks. via `clear_all_data.py`): `text_content` tømmes også. Da vil `search_documents` returnere tomt inntil dokumenter er importert på nytt.

**Re-import av dokumenter:** Bruk eksisterende dokumentimport-flyt (admin/upload, CSV-import av dokumenter, eller tilsvarende).

### KI-Kollega ved dataendring

KI-Kollega bruker samme `DATABASE_URL` som resten av backend. Kostnadsdata i enkel modus hentes nå med prioritet: `gl_transactions` > `property_husleie_csv` > `external_data.financials`. Se [KI_KOLLEGA_DATA_OG_FUNKSJON.md](KI_KOLLEGA_DATA_OG_FUNKSJON.md).
