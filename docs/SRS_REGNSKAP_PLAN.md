# SRS-Kompatibel Regnskapsmodul — Implementasjonsplan
*Sist oppdatert: 2026-03-20*

## Mål
Transformere 136 055 GL-linjer fra Agresso (Eiendomfebruar.csv) til et SRS-kompatibelt
eiendomsregnskap for Bufetat. Åpningsbalanse 01.01.2025.

---

## Datagrunnlag

| Fil | Beskrivelse | Størrelse |
|-----|-------------|-----------|
| `finans/Eiendomfebruar.csv` | Hoved-GL fra Agresso | 136 055 linjer, 37 MB |
| `finans/koststed_eiendom_mapping.csv` | 572 koststed → region/adresse | 572 rader |

### GL-kolonner (Eiendomfebruar.csv)
```
BA, Bilagsnr, Bilagsdato, År, Periode, Innkjøpskategorier, Innkjøpskategorier(T),
Underkategorier, Underkategorier(T), Konto, Konto(T), Region, Dim1, Dim1(T),
Dim2, Dim2(T), Dim3, Dim4, Dim5, Dim6, Dim7, AV, Tekst, Beløp, Resk.nr, Resk.nr(T)
```

### Kontoer i datasettet
| Konto | Navn | SRS-behandling |
|-------|------|----------------|
| 1268 | Påkostninger leide lokaler | SRS 17 – Anleggsmiddel |
| 4960 | Investering | SRS 17 – Anleggsmiddel |
| 6300 | Leie lokaler andre utleiere | SRS 13 – Operasjonell leie |
| 6310 | Leie lokaler fra Statsbygg | SRS 13 – Operasjonell (spesialregel) |
| 6320–6398 | Andre lokalkostnader | Drift |
| 6630, 6632, 6662 | Strøm/energi | Drift |

### Koststed-mapping
- 572 unike Dim1-koder fordelt på: Øst (185), Sør (131), Nord (73), Vest (82), Midt (60), Bufdir (36), Ukjent (5)
- Mapping: `Dim1-kode → Koststed_Navn + Region + Eksempel_Adresse`

---

## FASE 1 — Datamodell: Koble eiendom ↔ koststed

**Kritisk mangel nå:** `Property`-modellen har ingen `koststed_kode`-felt.
`GLTransaction` har `department_code` men ingen `property_id`-kobling.

### 1a. Ny Alembic-migrasjon: Property-modell

Legg til på `Property`:
```python
koststed_kode       = Column(String(20), nullable=True, index=True)   # Dim1-kode fra Agresso
koststed_navn       = Column(String(200), nullable=True)               # Dim1(T)
leiekontrakt_utlop  = Column(Date, nullable=True)                      # Påkrevd for SRS 17
```

### 1b. Ny Alembic-migrasjon: GLTransaction-modell (full erstatning)

Slett og gjenoppbygg `gl_transactions` med disse kolonnene:

```python
# Primærnøkler og sporing
transaction_id      = UUID PK
batch_id            = String(50)       # agresso_batch_id – sporing av importbunt
imported_by         = String(100)      # bruker-e-post
source_file_ref     = String(500)      # filnavn/blob-URL

# Agresso-felt (direkte fra CSV)
ba_kode             = String(10)       # BA – Bilagsart (IV, IW, LE, MT, osv.)
bilagsnr            = String(50)       # Bilagsnr – indeksert
bilagsdato          = Date
periode             = String(6)        # YYYYMM – ALLTID filtrer på dette, ikke dato
ar                  = Integer          # År (indeksert)
konto               = String(20)       # Konto-kode (indeksert)
konto_navn          = String(200)      # Konto(T)
region              = String(50)       # Region (Nord/Sør/Vest/Midt/Øst/Bufdir)
dim1_kode           = String(20)       # Koststed-kode (indeksert)
dim1_navn           = String(200)      # Koststed-navn
dim2_kode           = String(20)
dim2_navn           = String(200)
dim3_kode           = String(20)       # Formål
dim4_kode           = String(20)       # Finansiering (tildelingsbrev)
dim5_kode           = String(20)
dim6_anlegg_id      = String(20)       # Anleggsnummer (konto 1268/4960 PÅKREVD)
dim6_ansatt_id      = String(20)       # Ansattnummer (andre kontoer)
dim7_kode           = String(20)
av_konto            = String(20)       # Statskontoplan AV
tekst               = String(500)
belop               = Numeric(19,4)    # ALDRI Float – bruker Numeric
leverandor_id       = String(20)       # Resk.nr
leverandor_navn     = String(200)      # Resk.nr(T)

# Berikede felt (beregnet ved import)
property_id         = UUID FK nullable # Koblet via dim1_kode → Property.koststed_kode
srs_kategori        = String(20)       # 'Drift' | 'Investering' | 'Gjennomstrømning'
is_statsbygg        = Boolean          # True hvis leverandor_navn ILIKE '%statsbygg%'

# Immutabilitet
created_at          = DateTime
```

**Indekser:** `bilagsnr`, `konto`, `dim1_kode`, `periode`, `ar`

### 1c. Ny modell: KoststedMapping

```python
class KoststedMapping(Base):
    __tablename__ = "koststed_mapping"
    koststed_kode   = String(20) PK
    koststed_navn   = String(200)
    region          = String(50)
    eksempel_adresse = String(500)
    property_id     = UUID FK nullable   # Kobles manuelt eller via adresse-matching
```

---

## FASE 2 — Slett gammel data + import av rent datasett

### 2a. Slett (Supabase)
```sql
TRUNCATE TABLE gl_transactions CASCADE;
TRUNCATE TABLE budget CASCADE;
-- manual_expenses hvis den finnes
```

### 2b. Import-parser (`backend/scripts/import_gl_agresso.py`)

```
Algoritme:
1. Les Eiendomfebruar.csv (encoding=latin-1, delimiter=,)
2. For hver rad:
   a. Sanitér Beløp: fjern mellomrom-tusensep → Decimal
   b. Lookup property_id via dim1_kode → koststed_mapping.property_id
   c. Beregn srs_kategori:
      - konto in (1268, 4960)                → 'Investering'
      - konto in (6300..6398, 6630, 6632, 6662) → 'Drift'
      - ba_kode in (H1, H2, HB, RE)          → 'Gjennomstrømning'
   d. Sett is_statsbygg = leverandor_navn ILIKE '%statsbygg%'
   e. Sett dim6_anlegg_id hvis konto=1268/4960 og Dim6 ikke tom
3. Batchinsert 1000 rader om gangen med batch_id = timestamp+filnavn
4. Logg feil per rad, stopp IKKE hele importen
5. Balansesjekk per bilagsnr: SUM(belop) = 0 (for IV/IW/LE)
```

### 2c. Koble koststed → Property
```
1. Importer koststed_eiendom_mapping.csv → KoststedMapping-tabell
2. Forsøk adresse-matching: KoststedMapping.eksempel_adresse → Property.address
3. Manuelle treff (rest ~10%) via admin-UI
```

---

## FASE 3 — SRS-Beregningsmotor

### SRS 17 – Anleggsmidler

**Terskelregel:**
- Konto 1268/4960, beløp ≥ 50 000 kr → individuelt anleggsmiddel
- Konto 1268/4960, beløp < 50 000 kr, Tekst/Konto(T) inneholder "PC"/"Skjerm"/"IKT" → grupper per koststed + periode

**Avskrivningsformel (SRS 17 pkt 39):**
```
restlevetid_mnd = MIN(
    leiekontrakt_utlop - 01.01.2025,
    eiendelens_levetid   # standard 10 år / 120 mnd hvis ukjent
)
bokfort_verdi_01012025 = monthly_depr × restlevetid_mnd
monthly_depr = opprinnelig_kost / total_periodeLength_mnd
```

**Python-implementasjon (fra brukerspesifikasjon):**
```python
from dateutil.relativedelta import relativedelta
OPENING_BALANCE_DATE = datetime(2025, 1, 1)
DEFAULT_LEASE_END = datetime(2035, 1, 1)  # 10 år standard

def calculate_srs17(original_cost, purchase_date, lease_end_date):
    diff_total = relativedelta(lease_end_date, purchase_date)
    total_months = diff_total.years * 12 + diff_total.months
    if total_months <= 0:
        return 0, 0, 0
    monthly_depr = original_cost / total_months
    diff_remaining = relativedelta(lease_end_date, OPENING_BALANCE_DATE)
    remaining_months = diff_remaining.years * 12 + diff_remaining.months
    book_value = monthly_depr * remaining_months
    return book_value, remaining_months, monthly_depr
```

### SRS 13 – Leieavtaler
- `is_statsbygg = True` + konto 6310 → operasjonell leie (IKKE i balansen)
- Private utleiere (konto 6300) → forenklet metode, operasjonell

### SRS 10 – Nøytralisering (hjertet i løsningen)

For hver månedlig avskrivning på `monthly_depr` genereres to journalposteringer:
```
Postering 1 – Kostnad:
  Debet  60xx  (Avskrivning)
  Kredit 12xx  (Akkumulert avskrivning)

Postering 2 – Inntektsføring (nøytralisering):
  Debet  33xx  (Statens finansiering – utsatt)
  Kredit 39xx  (Inntektsføring av bevilgning)
```
**Uten denne logikken viser Bufetat kunstig underskudd.**

---

## FASE 4 — Anleggsregister (FixedAsset)

### Modell

```python
class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    asset_id            = UUID PK
    property_id         = UUID FK
    dim1_kode           = String(20)        # Koststed
    dim6_anlegg_id      = String(20)        # Agresso anleggsnummer
    beskrivelse         = String(500)
    konto               = String(20)        # 1268 / 4960

    # Verdier
    initial_value       = Numeric(19,4)     # Gjenanskaffelsesverdi ved åpningsbalanse
    book_value_opening  = Numeric(19,4)     # Bokført verdi 01.01.2025
    monthly_depreciation = Numeric(19,4)

    # Datoer
    purchase_date       = Date
    depreciation_start  = Date             # = 01.01.2025 for åpningsbalansen
    lease_end_date      = Date             # Fra Property.leiekontrakt_utlop

    # SRS 10
    offset_account      = String(20)       # Konto for nøytralisering (39xx)
    depr_account        = String(20)       # Avskrivningskonto (60xx)
    accum_depr_account  = String(20)       # Akkumulert avskrivning (12xx)

    # Status
    srs_status          = String(20)       # 'Aktiv' | 'Fullt_avskrevet' | 'Solgt'
    created_at          = DateTime
```

### Journalgenerator

Eksporter månedlige buntføringer til Agresso-format:
```
CSV-kolonner: BA, Konto, Dim1, Dim6, Beløp, Tekst, Periode
```

---

## FASE 5 — Frontend (ny, ren)

Sider som skal bygges:
1. **`/financials`** — Oversikt: Total portefølje, fordelt på Drift vs Investering vs Gjennomstrømning
2. **`/financials/koststed/[kode]`** — Alle GL-linjer for ett koststed
3. **`/financials/anlegg`** — Anleggsregister: liste + avskrivningsplan
4. **`/financials/srs`** — SRS-rapport: Balanse + Resultat etter nøytralisering
5. **`/properties/[id]`** — Koble eiendom til koststed + vis GL-historikk

---

## Sjekkliste før FASE 3

- [ ] Alle Properties har `koststed_kode` satt
- [ ] Alle Properties med konto 1268 har `leiekontrakt_utlop` (eller default 10 år)
- [ ] `KoststedMapping`-tabellen er populert (572 rader)
- [ ] `gl_transactions` er reimportert med korrekte felt
- [ ] `FixedAsset`-modellen finnes i DB
- [ ] Mapping konto 1268 → avskrivningskonto 60xx er definert

---

## Kritiske arkitekturregler

1. **Immutabilitet**: Aldri UPDATE/DELETE på `gl_transactions`. Feil rettes med RE/H1-bilag.
2. **Beløp**: `Numeric(19,4)` i Postgres — aldri `Float`.
3. **Ledende nuller**: Alle koder er VARCHAR. "0012" ≠ "12".
4. **Filtrer på `periode`** (YYYYMM), IKKE på `bilagsdato` — de kan avvike med år (SRS periodisering).
5. **Balansesjekk**: `SUM(belop) per bilagsnr = 0`. Valider per bilag, ikke per linje.
6. **Aldri named PG Enums** — bruk `Column(String)`.
7. **Logger**: Kun `logger.debug` på per-request tilgang — ikke `logger.info` (Railway rate-limit).
