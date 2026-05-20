# Regnskapslogikk og Systemkontekst

Dette dokumentet definerer de forretningsmessige reglene, datastrukturen og beregningslogikken for BEFS (Bufetat Eiendomsforvaltningssystem). Bruk dette som "Source of Truth" for all kode relatert til dataimport, validering og finansielle analyser.

---

## 1. Stack

| Lag | Teknologi | Hosting |
|---|---|---|
| Frontend | Next.js (App Router), TypeScript, TailwindCSS | Vercel |
| Backend / API | Python 3.11, FastAPI, SQLAlchemy 2 (async) | Railway |
| Database | PostgreSQL + pgvector | Railway |
| Auth | Supabase (session) + shared-secret Bearer (backend bypass) | Supabase |
| AI / Analyse | OpenAI GPT-4o via LangGraph, Python MCP-verktøy | Railway |

---

## 2. Datamodellens Arkitektur

Systemet er bygget på en hybridmodell mellom strukturerte stamdata og transaksjonelle regnskapsdata.

### A. Stamdata (`properties`-tabellen)

"Fasiten" – eiendomslisten.

- **Primærnøkkel:** `property_id` (UUID)
- **Regnskapskobling:** `lokalisering_id` (VARCHAR) mapper mot regnskapets `Dim 1 (Koststed)`
- **Nøkkelfelt for analyse:** `areal`, `kpi_justert_leie`, `tilstandsgrad`, `antall_ansatte`
- **Formål:** Nevner i KPI-beregninger (kostnad per kvm, income at risk)
- **JSONB:** `external_data`-feltet brukes for fleksible finansdata med varierende struktur

### B. Transaksjonsdata (`gl_transactions`-tabellen)

Inngående regnskapslinjer fra CSV-import (Xledger/Visma).

**Dimensjonsstruktur:**

| Dim | Kolonnenavn DB | Beskrivelse |
|---|---|---|
| Dim 1 | `dim1_koststed` | Koststed → bindeledd til `properties.lokalisering_id` |
| Dim 2 | `dim2_prosjekt` | Prosjektnummer |
| Dim 3 | `dim3_formal` | Formålskode |
| Dim 4 | `dim4_finansiering` | Finansieringskilde (SRS 10) |
| Dim 5 | `dim5_birknummer` | Birknummer |
| Dim 6 | `dim6_ansatt_id` + `dim6_anlegg_id` | **To kolonner** – se Dim 6-logikk nedenfor |
| Dim 7 | `dim7_avtalenummer` | Kontraktreferanse |

**Viktige felter:**

| Felt | Type | Notat |
|---|---|---|
| `bilagsnummer` | VARCHAR | Grouping-nøkkel (alle linjer med samme nr = én faktura) |
| `bilagsart` | VARCHAR | IV/IW/LE=faktura, BH/BR=lønn/reise, MT=anlegg, RE=reversering |
| `konto` | VARCHAR | AV (Art) – alltid string, aldri integer (ledende nuller) |
| `belop` | NUMERIC(19,4) | Aldri float/double |
| `periode` | VARCHAR(6) | YYYYMM – **bruk alltid dette for rapporter, ikke `bilagsdato`** |
| `leverandor_id` | VARCHAR | Resk.nr – kobling til leverandørregister |
| `batch_id` | UUID | Sporer hvilken import-batch linjen kom fra |
| `original_bilag_id` | UUID (nullable) | Self-referential FK for omposteringer |

**Uforanderlighet:** Regnskapsdata skal aldri UPDATE/DELETE. Feil rettes med nytt bilag (`bilagsart = RE` eller `H1/H2/HB`).

---

## 3. Dim 6 – Polymorfisk Validering

Dim 6 har to mulige tolkninger basert på konto:

```
Hvis konto ∈ anleggslisten → dim6_anlegg_id  (PÅKREVD)
Ellers                      → dim6_ansatt_id  (valgfritt)
```

**Anleggskontoer (krever `dim6_anlegg_id`):**

| Kontoområde | Beskrivelse |
|---|---|
| 1040–1298 | Aktiverte anleggsmidler og avskrivninger |
| 3800–3810 | Salg og gevinst anlegg |
| 4930–4999 | Investeringer og systemkonti anlegg |
| 6000–6071 | Avskrivninger og nedskrivninger |
| 6551 | Bærbare PC-er (småanskaffelser/anlegg) |
| 7800 | Tap ved avgang |

**SRS-referanse:** SRS 17 (Anleggsmidler) – grense 50 000 kr + ≥3 år levetid for aktivering.

---

## 4. Bilagsarter – Validering

| Kode(r) | Funksjon | Systemregel |
|---|---|---|
| IV, IW, LE | Inngående faktura | Valider mot leverandørreskontro; sum per bilagsnummer = 0 |
| BH, BR | Lønn / Reise | Dim 6 = Ansattnummer; periodiser på arbeidsperiode (SRS 25) |
| MT | Anleggstransaksjon | Konto MÅ finnes i anleggslisten; Dim 6 = Anleggsnummer |
| FA | Kundefaktura | Valider mot kundereskontro |
| H1, H2, HB | Omposteringer | Skann beskrivelsesfeltet etter opprinnelig bilagsnummer (IV) |
| RE | Reversering | Speiler opprinnelig bilag med negativt fortegn |
| CA, CF, KF, OP | **UTGÅTT** | Avvis med feilmelding "Bilagsart utgått" |

---

## 5. Finansielle KPI-regler

### 5.0 Areal- og Kapasitetsnøkkeltall

```
Kvm per bruker/ansatt = Areal / (Kapasitet || Antall_ansatte)
Bad per bruker        = Antall_bad / Kapasitet
```

### 5.1 Cost-to-Rent Ratio

```
Ratio = Total Driftskostnad / Total Leieinntekt
< 0.8  → OK
0.8–1.0 → Advarsel
> 1.0  → Kritisk
```

### 5.2 Konto → Kategorimapping (Sekkeposter)

Kategorisering baseres alltid på **konto (AV)**, aldri leverandørnavn.

| Kontoområde | Kategorinavn | Stamdata-benchmark |
|---|---|---|
| 6300 | Husleie | `kpi_justert_leie` |
| 6320 | Renhold | `renhold_estimat` |
| 6340 | Energi/Strøm | `energi_estimat` |
| 6390 | Vedlikehold | `vaktmester_estimat` |
| 6000–6071 | Avskrivninger | Beregner bokført verdi |
| 1000–1299 | Anleggsmidler | Aktiverer anleggslogikk |
| 4930–4999 | Investeringer | Capital Expense-budsjett |

### 5.3 KPI-indeksregulering

Valider om faktisk betalt leie (konto 6300) samsvarer med `kpi_justert_leie` fra stamdata, justert for `oppstartsdato`. Avvik > 5 % gir advarsel.

### 5.4 Data Quality Status

Klassifiser eiendommer etter datakvalitet for rapportering og prioritering:

| Status | Kriterium |
|---|---|
| **Komplett** | Finnes både kostnadslinjer (konto 6xxx) og leiepostinger (konto 6300) |
| **Mangler husleie** | Finnes kostnader, men ingen 6300-posteringer i perioden |
| **Mangler alt** | Ingen GL-transaksjoner koblet til eiendommen i perioden |

```sql
-- Finn eiendommer uten noen GL-data i en gitt periode
SELECT p.property_id, p.name
FROM properties p
WHERE NOT EXISTS (
    SELECT 1 FROM gl_transactions g
    WHERE g.dim1_koststed = p.lokalisering_id
      AND g.periode = '202506'
);
```

### 5.5 Periodisering

Filtrer alltid rapporter på `periode` (VARCHAR YYYYMM), **ikke** `bilagsdato`. De kan avvike med hele år (statlig SRS-praksis).

---

## 6. Heuristic Linking – Omposteringer

Bilagsarter H1, H2, HB mangler leverandør-ID i reskontro.

**Algoritme:**
1. Skann `beskrivelse`-feltet for tall som matcher eksisterende `bilagsnummer` fra IV-bilag
2. Bygg relasjon: `Ompostering.bilagsnummer → OriginalBilag.leverandor_id`
3. Flagg linjen i UI med opprinnelig leverandør

**DB-kobling:** `gl_transactions.original_bilag_id → gl_transactions.transaction_id` (self-referential FK, nullable)

---

## 7. Dataintegritets-regler (Teknisk)

- **Beløp:** `NUMERIC(19,4)` i Postgres, `Decimal` i Python. Aldri `float`.
- **Koder:** Alle dimensjonskoder og kontoer er `VARCHAR`. Ledende nuller MÅ bevares (`"0100"` ≠ `"100"`).
- **Balansesjekk:** Sum av alle linjer per `bilagsnummer` = 0 (Debit + Kredit).
- **Indekser:** Obligatorisk på `bilagsnummer`, `konto`, `dim2_prosjekt`, `periode`.
- **Audit trail:** Lagre `batch_id` (UUID), `imported_by` (user_id) og `source_file_ref` per import-batch.
- **MVA:** `avgiftstype = H` → kostnad føres netto på dimensjonene; 25 % MVA skilles ut separat.

---

## 8. Eksisterende MCP-verktøy (backend)

Fil: `backend/app/services/mcp/handler.py`

| Verktøy | Beskrivelse |
|---|---|
| `finans_get_expiring_contracts` | Income at Risk – kontrakter som utløper < 90 dager |
| `finans_find_cost_anomalies` | Eiendommer med kostnader > 50 % over regionsnitt |

---

## 9. Eiendomsspesifikke Krav – Utvidet Property-modell

Følgende felt mangler i eksisterende Property-modell og krever Alembic-migrasjon:

### Kategorisering

| Felt | Type | Verdier |
|---|---|---|
| `type_eiendom` | VARCHAR | Formålsbygg, Næringslokaler, Familievernkontor |
| `eierstruktur` | VARCHAR | Statsbygg, Privat |
| `brukerenhet` | VARCHAR | Nord, Sør, Midt, Vest, Øst, Bufdir |
| `plastype` | VARCHAR | Akutt, Atferd høy, Atferd lav, Rus, EMA |
| `kapasitet` | Integer | Antall plasser |
| `faktisk_bruk` | Integer | Faktisk belegg |

### Fasiliteter (Boolean)

| Felt | Type | Merknad |
|---|---|---|
| `har_familieleilighet` | Boolean | |
| `har_treningshybel` | Boolean | |
| `har_parkering` | Boolean | |
| `antall_parkeringsplasser` | Integer | nullable |

### Kart og Geokoding (GIS)

| Felt | Type | Merknad |
|---|---|---|
| `breddegrad` | NUMERIC(10,7) | Fylles via geocoding-jobb (Kartverket API) |
| `lengdegrad` | NUMERIC(10,7) | Fylles via geocoding-jobb |
| `byggeaar` | Integer | Hentes fra Kartverket Matrikkel-API (Gnr/Bnr) |
| `avstand_politi_km` | NUMERIC(6,2) | Blålys-analyse |
| `avstand_sykehus_km` | NUMERIC(6,2) | Blålys-analyse |
| `avstand_brann_km` | NUMERIC(6,2) | Blålys-analyse |
| `avstand_legevakt_km` | NUMERIC(6,2) | Blålys-analyse |
| `avstand_skole_km` | NUMERIC(6,2) | Blålys-analyse |

**Kartteknologi:** Leaflet / Mapbox. Koordinater hentes via Kartverkets geocoding-API.

**Kart-fargekoding:**
- Eierstruktur: Grønn = Statsbygg, Gul = Privat
- Type: Separate ikoner per `type_eiendom`

### Dokumentasjon og Fase

| Felt | Type | Merknad |
|---|---|---|
| `arkiv_link` | VARCHAR | URL til saksmappen i Elements |
| `prosjektfase` | VARCHAR | Planlegging, Utførelse, Ferdigstilt |

---

## 10. Kontraktslogikk – MNOK 1,4-regelen ("Vesentlige avtaler")

Rapport som henter ut vesentlige leieavtaler for revisjon og rapportering til departementet.

### Kriterier

```
Totalverdi = Husleie + Felleskostnader + BAD + Parkering + Indre vedlikehold > 1 400 000 NOK
OG startdato IN (2023, 2024, 2025)
```

*BAD = Brukeravhengig drift (strøm, renhold, o.l. fakturert separat fra husleie)*

### SQL-implementasjon

```sql
SELECT
    contract_id,
    property_id,
    start_date,
    (annual_rent
     + COALESCE(felleskostnader, 0)
     + COALESCE(bad_kostnad, 0)
     + COALESCE(parkering_kostnad, 0)
     + COALESCE(vedlikehold_kostnad, 0)
    ) AS totalverdi
FROM contracts
WHERE EXTRACT(YEAR FROM start_date) IN (2023, 2024, 2025)
  AND (annual_rent
       + COALESCE(felleskostnader, 0)
       + COALESCE(bad_kostnad, 0)
       + COALESCE(parkering_kostnad, 0)
       + COALESCE(vedlikehold_kostnad, 0)
      ) > 1400000
ORDER BY totalverdi DESC;
```

### Navnestandard (Kontrakt-ID)

Format: `BUF-[REGION]-[ÅR]-[KOMMUNENR]-[S/P]-[TYPE]`

| Posisjon | Verdi | Eksempel |
|---|---|---|
| REGION | Nord/Sør/Midt/Vest/Øst | NORD |
| ÅR | Startår | 2024 |
| KOMMUNENR | 4-sifret kommunenummer | 1804 |
| S/P | Statsbygg / Privat | S |
| TYPE | FM=Formålsbygg, KO=Kontor, FV=Familievern | FM |

**Eksempel:** `BUF-NORD-2024-1804-S-FM`

```python
def generer_kontrakt_id(region: str, aar: int, kommunenr: str, eierstruktur: str, type_eiendom: str) -> str:
    type_kode = {"Formålsbygg": "FM", "Næringslokaler": "KO", "Familievernkontor": "FV"}.get(type_eiendom, "XX")
    eier_kode = "S" if eierstruktur == "Statsbygg" else "P"
    return f"BUF-{region.upper()}-{aar}-{kommunenr}-{eier_kode}-{type_kode}"
```

---

## 11. Avansert Logikk & Integritetssjekker

### 11.1 Areal-validering (KRITISK – påvirker alle KPIer)

```
Netto Areal = Eksklusivt_Areal + Fellesareal + Tilleggsareal - Reduksjonsareal
```

Dette tallet SKAL brukes som nevner i **alle** kr/kvm-beregninger. Feil her gjør alle KPIer feil.

```python
def netto_areal(eksklusivt: Decimal, felles: Decimal, tillegg: Decimal, reduksjon: Decimal) -> Decimal:
    return eksklusivt + felles + tillegg - reduksjon
```

DB-felt som kreves på `properties`: `eksklusivt_areal`, `fellesareal`, `tilleggsareal`, `reduksjonsareal` (alle `NUMERIC(10,2)`).

### 11.2 Kontrakts-automatisering

- **Opsjonsvarsling:** Cron-jobb (Railway) trigger ved `sluttdato - 365 dager`. Sender varsel til saksbehandler (e-post / Elements) om utløpende kontrakt med opsjon.
- **KPI-sjekk:** Systemet skal flagge dersom konto 6300 (Leie) endrer seg i regnskapet uten at det foreligger en registrert KPI-regulering i stamdata (`kpi_justert_leie`).

### 11.3 SCD – Historisk Versjonering av Stamdata

Eksisterende modell overskriver data. Eiendomsforvaltning krever historisk sporbarhet (f.eks. "hva var arealet før ombyggingen i 2024?").

**Løsning – Effective Dating:**

Legg til `valid_from DATE` og `valid_to DATE NULLABLE` på `properties`. Ny rad ved endring; `valid_to` settes på gammel rad.

```sql
-- Hent stamdata slik de var 1. januar 2023
SELECT * FROM properties
WHERE property_id = $1
  AND valid_from <= '2023-01-01'
  AND (valid_to IS NULL OR valid_to > '2023-01-01');
```

**Alternativ (enklere):** Lagre endringslogg i en `property_history`-tabell med `changed_at TIMESTAMPTZ`, `changed_by`, `field_name`, `old_value`, `new_value`.

### 11.4 Admin Data-berikelse (manuell input)

Eksisterende admin-dashboard (`/admin`) bør utvides med et "Eiendomsberikelse"-skjema der forvalter kan registrere:
- Arealkomponenter (eksklusivt, felles, tillegg, reduksjon)
- Fasiliteter og fasetype
- Prosjektfase og arkiv-lenke
- Tilstandsgrad og kapasitet

Dette gir regnskapet sin "mangler-du" kontekst (hva som ble betalt og *hvorfor*).

---

*Sist oppdatert: 2026-02-20*
