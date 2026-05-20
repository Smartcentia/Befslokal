# Budsjett 2026 – Estimeringsmetodikk

Dette dokumentet beskriver metodikken som er brukt for å generere budsjett 2026
basert på faktiske GL-regnskapsdata fra 2025.

---

## Resultat

| | 2025 faktisk | Rate | 2026 budsjett |
|---|---:|---:|---:|
| **Husleie** | 364 360 443 NOK | +4,7 % | 381 485 383 NOK |
| **Drift/andre kost.** | 203 162 059 NOK | +10,0 % | 223 478 264 NOK |
| **TOTALT** | **567 522 501 NOK** | **+6,6 %** | **604 963 648 NOK (~605 MNOK)** |

Vekst totalt: **6,6 %**
Budsjettlinjer i DB: **1 776** (74 eiendommer × 12 måneder × 2 kategorier)

---

## Metodikk: Kategori-basert GL-estimering

### Bakgrunn

Tidligere budsjett (523 MNOK) var basert på Innkjøpsanalyse-CSV med kontrakts-fallback.
Dette undervurderte faktiske kostnader fordi:
- Innkjøpsanalyse dekket kun 38 eiendommer (105 MNOK primær, 418 MNOK fallback)
- Resultatet var **lavere** enn faktisk forbruk i 2024 og 2025

Ny metodikk bruker **faktisk GL-regnskap 2025** som basis – den eneste kilden som
dekker 100 % av faktiske kostnader.

### Vekstrater (analysert fra GL)

| Kategori | 2024 faktisk | 2025 faktisk | Vekst | Brukt rate |
|---|---:|---:|---:|---:|
| Husleie | 347 047 000 | 364 360 000 | +4,99 % | **+4,7 %** |
| Drift/andre | 184 690 000 | 203 162 000 | +9,99 % | **+10,0 %** |

Husleie-raten (4,7 %) samsvarer med kontraktsjusteringer (KPI-basert).
Drift-raten (10,0 %) reflekterer økte tjeneste- og materiellkostnader.

### Kostnadskategorisering

To kategorier basert på `account_name` i `gl_transactions`:

**Husleie** – kontoer som klassifiseres som leiekostnad:
- Leie lokaler fra Statsbygg
- Leie lokaler andre utleiere
- Leie parkeringsplass
- Leie av lager/naust/garsjer og lignende
- Husleie
- Enhver `account_name` som starter med «Leie »

**Drift** – alle øvrige kontoer (fellesutgifter, strøm, renhold, vedlikehold m.m.)

Klassifiseringen utføres av `is_lease_account()` i `app/models/gl_constants.py`.

### Proporsjonal fordeling av sentralt bokførte kostnader

**Problem:** 84 % av GL-kostnadene (475 MNOK) er bokført på sentrale Koststed-koder
uten direkte `property_id`. Dette er reelle eiendomskostnader (husleie, strøm,
renhold m.m.) som Bufetat bokfører per region/direktørområde, ikke per eiendom.

**Løsning:** Orphan-kostnadene fordeles proporsjonalt til kjente eiendommer basert
på eiendommens andel av totale direkte (property-linkede) kostnader.

```
Eiendom A sin andel = (A direkte kost) / (totale direkte kost)
A allokert sentralt  = orphan_husleie × A_andel  +  orphan_drift × A_andel
A total 2025 basis   = A direkte + A allokert sentralt
```

**GL-fordeling 2025:**
- Direkte eiendomslinket: 105 558 323 NOK (74 eiendommer)
- Sentrale Koststed-koder: 461 964 178 NOK (fordelt proporsjonalt)
- Total GL 2025: **567 522 501 NOK**

### Månedsfordeling

**Husleie:** Likt fordelt over 12 måneder (`h_base / 12`).

**Drift:** Sesongfordelt med faktorer som reflekterer høyere forbruk vinter/høst:

| Mnd | Jan | Feb | Mar | Apr | Mai | Jun | Jul | Aug | Sep | Okt | Nov | Des |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| Faktor | 1,15 | 1,15 | 1,05 | 0,95 | 0,90 | 0,80 | 0,75 | 0,80 | 0,95 | 1,05 | 1,15 | 1,15 |

Sum faktorer = 12,0 (normalisert til 100 % av årsbudsjettet).

---

## Databeskrivelse

Budsjettlinjer lagres i `budget`-tabellen med:

| Felt | Verdi |
|---|---|
| `year` | 2026 |
| `month` | 1–12 |
| `category` | `husleie` \| `drift` |
| `amount` | Beregnet beløp per måned |
| `is_synthetic` | `true` |
| `data_source` | `gl_2025_husleie+4.7pct_alloc` \| `gl_2025_drift+10.0pct_alloc` |

---

## Script

```bash
cd backend

# Dry-run – beregn og vis rapport (ingen DB-endringer)
python3 scripts/budget_2026_kategori.py --dry-run

# Kjør og skriv til database
python3 scripts/budget_2026_kategori.py
```

**Fil:** `backend/scripts/budget_2026_kategori.py`

---

## Sammenligning med tidligere metoder

| Metode | Sum | Grunnlag | Problem |
|---|---:|---|---|
| Kontrakts-fallback | 523 MNOK | Kontraktsverdier + Innkjøpsanalyse | Lavere enn faktisk forbruk 2024 og 2025 |
| Innkjøpsanalyse + fallback | 523 MNOK | CSV + kontrakter | Dekker kun 38 eiendommer primært |
| **GL kategori-basert (nåværende)** | **605 MNOK** | GL 2025 + proporsjonal allokering | **Anbefalt – full datadekning** |

---

## Relaterte filer

| Fil | Beskrivelse |
|---|---|
| `backend/scripts/budget_2026_kategori.py` | Hoved-script for budsjettgenerering |
| `backend/scripts/estimate_budget_2026.py` | Eldre script (Innkjøpsanalyse-basert) |
| `backend/app/models/gl_constants.py` | `is_lease_account()`, `LEASE_ACCOUNT_NAMES` |
| `backend/app/services/budget_generation_service.py` | Generell budsjett-service |
| `docs/MASTER_REGNSKAP.md` | Datakilder og struktur |
| `docs/FINANSIELL_BEREGNINGS_DOKUMENTASJON.md` | KPI-formler og beregningsmetoder |
