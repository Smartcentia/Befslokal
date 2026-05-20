# Teknisk dokumentasjon — Budsjettprediksjon 2027

**System:** BEFS / KNOWME
**Modul:** Økonomi → Prediksjon 2027
**Sist oppdatert:** 2026-04-09 (v3 — innkjøpsanalyse-import, Excel-eksport, interaktiv budsjettside, RBAC åpnet)
**Ansvarlig:** Systemadministrator / Økonomiansvarlig

---

## 1. Formål

Systemet beregner automatisk budsjettestimater for alle eiendommer i Bufetat-porteføljen for målåret 2027. Estimatene brukes som datagrunnlag i budsjettprosessen og lagres i `budget`-tabellen for videre bruk i rapporter og analyser.

---

## 2. Algoritme: Holt's Linear Exponential Smoothing

### 2.1 Metodevalg

Systemet bruker **Holt's Linear Method** (også kalt Double Exponential Smoothing), utvidet med **Gardner-McKenzie trend-demping (1985)**. Metoden er valgt fordi den:

- Gir nyere år mer vekt enn eldre år (eksponentiell vekting)
- Fanger opp både *nivå* (gjennomsnittlig kostnadsnivå) og *trend* (retning og tempo i endringen)
- Ikke krever sesongkomponent på årsdata
- Er robust for datakvalitetsproblemer som manglende år

### 2.2 Matematisk formulering

**Nivåoppdatering:**
```
L_t = α · y_t + (1 − α) · (L_{t−1} + T_{t−1})
```

**Trendoppdatering:**
```
T_t = β · (L_t − L_{t−1}) + (1 − β) · T_{t−1}
```

**Prognose med demping (Gardner-McKenzie):**
```
Forecast(h) = L_n + (φ¹ + φ² + ... + φʰ) · T_n
```

Der:
| Parameter | Verdi | Betydning |
|---|---|---|
| `α` (alpha) | 0,70 | Nivå-glattning. 70 % vekt på siste faktiske år. |
| `β` (beta) | 0,30 | Trend-glattning. Demper trendestimering. |
| `φ` (phi) | 0,85 | **Gardner-McKenzie 1985.** Reduserer trend-overshoot. For h=2: multiplikator = 0,85+0,7225 = 1,5725 (vs. 2,0 uten demping). |
| `h` (horizon) | 2 | Antall år frem til målåret (2025→2027). |
| `max_growth_factor` | 5,0 | Safety cap: forecast aldri mer enn 5× siste faktiske år per kategori. |
| `cold_start_ratio` | 3,0 | **Cold-start filter.** Hvis `siste_år / mean(serie) > 3,0`, brukes inflasjonsfallback. Fanger opp nyåpnede/reaktiverte eiendommer. 0 = deaktivert. |
| Inflasjonsfallback | 3,5 % | SSB KPI-estimat — brukes for eiendommer med kun 1 år historikk **eller** cold-start. |

### 2.3 Fallback-logikk

| Tilgjengelige år | Betingelse | Metode | method-felt |
|---|---|---|---|
| 0 år | — | Hoppes over | — |
| 1 år | — | `last_year × (1 + inflation × h)` | `inflation_fallback` |
| 2+ år | `siste / mean > cold_start_ratio` | `last_year × (1 + inflation × h)` | `inflation_coldstart` |
| 2 år | Normal | Én Holt-iterasjon + demping | `holt_linear_damped` |
| 3+ år | Normal | Full Holt's Linear + demping + cap | `holt_linear_damped` |

### 2.4 Cold-start filter (nytt v2)

**Problem:** Eiendommer som går fra inaktiv til full drift (f.eks. nyåpning 2024) gir Holt-Winters en falsk eksplosiv trend. Eksempel: Skatval predikert til +272 % uten filter.

**Løsning — heuristikk:**
```
cold_start = (series[-1] / mean(series)) > cold_start_ratio
```

Hvis betingelsen er sann, tolkes eiendommen som "rampende opp" og inflasjonsfallback brukes:
```
forecast = series[-1] × (1 + 0.035 × horizon)
```

**Eksempel Skatval:**
```
Serie:  [1K, 10K, 50K, 3M, 5.5M]
Mean:   1.72M
Ratio:  5.5M / 1.72M = 3.2  >  terskel 3.0  → cold-start
→ Forecast = 5.5M × (1 + 0.035 × 2) = 5.96M  (+7%)
→ Uten filter: 20.7M  (+272%)
```

**Effekt på portefølje (lokal test):**
| Eiendom | Uten filter | Med filter (v2) | Metode |
|---|---|---|---|
| Skatval | +272 % | +7 % | inflation_coldstart |
| Toppen | +175 % | +7 % | inflation_coldstart |
| Nes | +4 % | +4 % | holt_linear_damped (uberørt) |
| Vik | +6 % | +5 % | holt_linear_damped (uberørt) |

---

## 3. Datagrunnlag

### 3.1 Kilde
- **Tabell:** `gl_transactions` (Agresso GL, importert via BUFDIR-pipeline)
- **Filter:** `belop > 0 AND property_id IS NOT NULL AND ar BETWEEN 2021 AND 2025`
- **Gruppering:** Per `property_id` × `srs_kategori` × `ar`

### 3.2 Kategorier
| `srs_kategori` (GL) | `category` (budget) | Beskrivelse |
|---|---|---|
| Drift | operations | Strøm, renhold, vaktmester, vedlikehold |
| Investering | investment | Påkostninger, større rehabilitering |
| Gjennomstrømning | property | Husleie videreformidlet til gårdeier |
| (ingen / ukjent) | other | Ikke-kategoriserte kostnader |

### 3.3 Dekningsgrad
- **Eiendommer predikert:** 118 av ca. 400 totalt
- **GL-volum matchet:** ca. 410M NOK av 568M NOK total GL 2025 (72 %)
- **Ikke-matchet (28 %):** Koststed uten `property_id`-kobling i `koststed_mapping`-tabellen

---

## 4. Månedlig fordeling

Etter at årsbudsjettet er beregnet, fordeles det på 12 måneder basert på **historisk månedsmønster** for den spesifikke eiendommen og kategorien:

```
monthly_weight[m] = hist_avg[m] / sum(hist_avg[1..12])
```

Fallback: Uniform fordeling (1/12) dersom historisk månedsmønster mangler.

---

## 5. Datalagrring

Prediksjoner lagres i `budget`-tabellen:

| Kolonne | Verdi |
|---|---|
| `is_synthetic` | `true` |
| `data_source` | `holt_winters_2027` |
| `year` | 2027 |
| `month` | 1–12 (12 rader per eiendom per kategori) |
| `amount` | Månedlig beløp (NOK) |

Eksisterende syntetiske rader for samme `property_id / year / category / data_source` slettes og skrives på nytt ved kjøring.

---

## 6. API-endepunkter

### Generer prediksjon (kjøres av admin)
```
POST /api/v1/financials/predict-budget
Authorization: Bearer <token>

{
  "year": 2027,
  "alpha": 0.7,
  "beta": 0.3,
  "inflation": 0.035,
  "phi": 0.85,
  "max_growth_factor": 5.0,
  "cold_start_ratio": 3.0,
  "history_from": 2021
}
```
Returnerer: `{ "processed": 118, "skipped": 0, "errors": [], "year": 2027 }`

**Krever ADMIN-rolle. Tar ca. 2–3 minutter.**
**NB:** Endepunktet bruker `asyncio.shield()` — prediksjonen fullfører selv om klienten timeouter. Sjekk resultatet via `GET /prediksjon-2027` etter 3 minutter.

### Hent sammendrag
```
GET /api/v1/financials/prediksjon-2027
Authorization: Bearer <token>
```
Returnerer: Total, per region, topp 20 eiendommer, per kategori, sanity-sjekk + lønnsprediksjon.
**Alle roller — ingen rolle-sjekk (read-only).**

### Lønnsprediksjon
```
POST /api/v1/financials/salary-costs/predict?year=2027
Authorization: Bearer <token>
```
Kjører Holt-Winters separat på lønnsserien. Lagrer til `salary_costs` med `import_batch_id='holt_winters_2027'`.
**Produksjonsstall (apr 2026):** lonn_2027 = 645,3 MNOK (+30,5 % vs 2025)

### Excel-eksport
```
GET /api/v1/financials/prediksjon-2027/export.xlsx?scenario=xgb70
Authorization: Bearer <token>
```
Returnerer en XLSX-fil med 5 ark: Antagelser (justerbare), Per region (formler), Per kategori, Topp 20 eiendommer, Rådata Holt-Winters.
Krever `openpyxl>=3.1.0` i `requirements.txt`.

---

## 7. Sanity-sjekk

Systemet kjører automatisk følgende valideringer etter prediksjon:

| Sjekk | Grense | Handling |
|---|---|---|
| Eiendom har 2027 > 2× 2025 | >100 % vekst | Merkes som outlier i rapport |
| Totalt avvik fra 2025 | Brukes som indikatortall | Vises i sanity-panel |
| Eiendommer uten prediksjon | Antall | Vises i rapport |

---

## 8. Outlier-håndtering

### 8.1 Hva er en outlier?
En eiendom der predikert 2027-kostnad er mer enn 2× faktisk 2025-kostnad.

### 8.2 Årsaker
- **Cold-start:** Eiendom gikk fra inaktiv/lav aktivitet til full drift i 2024–2025. Algoritmen tolker nivåhoppet som en sterk trend.
- **Engangsutgifter:** Store rehabiliteringskostnader i 2024–2025 som ikke er representative.
- **Datakvalitet:** Feilkategoriserte transaksjoner i GL.

### 8.3 Teknisk forklaring (cold-start)
For en eiendom med serie `[0, 0, 0, 2M, 5.5M]`:
- Nivå etter 2025: `L ≈ 5.1M` (sterkt vektet mot siste år)
- Trend etter 2025: `T ≈ 3.5M/år`
- Forecast 2027: `5.1M + 1.57 × 3.5M = 10.6M`
- 5× cap: `5.5M × 5 = 27.5M` — cap trigges ikke (10.6M er under)

### 8.4 Anbefalte korreksjoner (manuell)
For outlier-eiendommer: bruk **20 % vekst fra 2025-verdi** som konservativt estimat, med mindre det finnes kjent grunnlag for høyere vekst.

### 8.5 Implementerte forbedringer (v2 — mars 2026)
- ✅ **Cold-start ratio filter** (`cold_start_ratio=3.0`): Fanger opp rampende eiendommer
- ✅ **Gardner-McKenzie trend-demping** (`phi=0.85`): Demper trend-overshoot 21 %
- ✅ **Safety cap** (`max_growth_factor=5.0`): Absolutt tak på 500 % vekst per kategori
- ✅ **asyncio.shield()**: Prediksjonen fullfører selv ved TCP-timeout

### 8.6 Fremtidig forbedring (planlagt)
- Minimum-aktivitetssjekk: Krev minst 2 år med `belop > 100 000` for full Holt-kjøring
- Syntetisk "Sentralt/Ufordelt"-eiendom for de 158M NOK som mangler `property_id`
- Konfidensintervall: Beregn ±σ rundt prediksjon basert på historisk variasjon

---

## 9. Validering og kvalitetssikring

### Manuelle kontroller som bør gjøres
1. **Totalsum:** Korrigert 2027-estimat bør ligge mellom 430M og 500M NOK (matchet base)
2. **Regionfordeling:** Ingen region bør ha >40 % vekst (med mindre kjent årsak)
3. **Outlier-liste:** Gjennomgå alle 10 flaggede eiendommer manuelt
4. **Kategorisplit:** Drift bør utgjøre >80 % av totalen

### Produksjonstall (april 2026 — verifisert)
| Mål | Verdi |
|---|---|
| Eiendomsdrift 2027 | **614,8 MNOK** |
| 2025 GL (grunnlag) | 530,5 MNOK |
| Vekst eiendom % | +15,9 % |
| Lønnskostnader 2027 | **645,3 MNOK** |
| Lønnskostnader 2025 | 494,7 MNOK |
| Vekst lønn % | +30,5 % |
| Totalt budsjettbehov | **~1 260 MNOK** |
| Antall eiendommer | 190 |
| Outliers (>2×2025) | 7 (Skjerven rusbehandling, Skjoldvegen, Vikhovlia m.fl.) |

Region-fordeling: Sør 255,6M | Midt-Norge 124,4M | Nord 112,5M | Vest 69,3M | Øst 51,5M | Bufdir 1,4M

---

## 10. Kodefiler

| Fil | Funksjon |
|---|---|
| `backend/app/services/prediction_service.py` | Kjernealgoritme: `_holt_linear_forecast()`, `predict_all_properties()` |
| `backend/app/services/salary_prediction_service.py` | Holt-Winters for lønn, SALARY_INFLATION=0.045 |
| `backend/app/services/financials/prediksjon_2027_export.py` | Excel-eksport med openpyxl (5 ark, justerbare formler) |
| `backend/app/api/v1/budget_prediction.py` | API-endepunkt POST /predict-budget |
| `backend/app/api/v1/financials.py` | GET /prediksjon-2027, GET /salary-costs, GET /prediksjon-2027/export.xlsx |
| `backend/app/models/financial_models.py` | InnkjopNasjonalSummary, SalaryCost (+ data_source, is_partial_year) |
| `backend/alembic/versions/20260408_innkjop_import_tables.py` | Migrasjon: innkjop_nasjonal_summary + salary_costs nye kolonner |
| `backend/scripts/import_innkjop_excel.py` | Importerer Innkjøpsanalyse 2026 Excel (lønn + innkjøp nasjonal) |
| `frontend/app/financials/prediksjon/page.tsx` | UI-side for prediksjon (sammendrag, region, topp 20) |
| `frontend/app/financials/prediksjon/budsjett/page.tsx` | Interaktiv budsjettjusteringsside (live-kalkulator) |

---

## 11. Referanser

- Gardner, E.S. & McKenzie, E. (1985). *Forecasting Trends in Time Series.* Management Science, 31(10), 1237–1246.
- Holt, C.E. (1957). *Forecasting Seasonals and Trends by Exponentially Weighted Moving Averages.* ONR Research Memorandum 52.
- SSB (2026). KPI-prognose 2026–2027: 3,5 % per år.
