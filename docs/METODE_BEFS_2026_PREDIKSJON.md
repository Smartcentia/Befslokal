# BEFS 2026 Prediksjon — Metodikk og Revisjonsspor

**Versjon:** 3 (gjeldende)  
**Dato:** 2026-05-07  
**Status:** I bruk i produksjon  

---

## Bakgrunn

BEFS beregner en uavhengig prediksjon for eiendomskostnader i 2026 som sammenlignes mot økonomiavdelingens vedtatte budsjett. Denne prediksjonen brukes til intern kvalitetssikring og tidlig varsling om avvik.

---

## Gjeldende metode (v3): Regionale vekstrater

### Datagrunnlag

| Kilde | Tabell | Filter |
|-------|--------|--------|
| Faktisk regnskap 2025 | `finance_budget` | `data_source='kontant_2025'`, `year=2025` |
| Økonomiavd. budsjett 2026 | `finance_budget` | `data_source='finance_dept_2026'`, `year=2026` |
| Prediksjoner 2026 (BEFS) | `budget` | `data_source='okonomi_regional_2026'`, `year=2026` |

### Fremgangsmåte

Vekstratene ble beregnet (2026-05-07) ved å sammenligne økonomiavdelingens vedtatte budsjett 2026 mot faktisk regnskap 2025, **aggregert per region** via `koststed_mapping`-tabellen:

```
vekstrate(region) = SUM(finance_dept_2026.amount) / SUM(kontant_2025.amount)
                    for alle koststeder i regionen
```

For hvert koststed i `finance_budget` (kontant_2025) er prediksjonen:

```
prediksjon(eiendom, måned, kategori) = kontant_2025(eiendom, måned, kategori) × vekstrate(region)
```

Regionen hentes fra `koststed_mapping.region` for eiendommen.

### Regionale vekstrater

| Region | Vekstrate | Forklaring |
|--------|-----------|------------|
| Øst | ×1.1701 (+17.01 %) | Økt kapasitet / nye institusjoner |
| Sør | ×0.8922 (−10.78 %) | Kapasitetsreduksjon i region |
| Nord | ×1.2662 (+26.62 %) | Stor kapasitetsvekst |
| Vest | ×0.8508 (−14.92 %) | Kapasitetsreduksjon |
| Midt-Norge | ×1.0213 (+2.13 %) | Stabil vekst |
| Bufdir | ×1.1423 (+14.23 %) | Direktoratsnivå, økt aktivitet |
| Nasjonal (fallback) | ×1.0350 (+3.50 %) | Prisjustering for eiendommer uten regionkobling |

Eiendommer uten match i `koststed_mapping` (30 stk.) fikk fallback-raten +3.5 %.

### Totaler per kategori

| Kategori | Kontant 2025 | BEFS Pred 2026 | Vekst |
|----------|-------------|----------------|-------|
| Lokaler  | ~415 MNOK   | 445.06 MNOK    | +7.2 % |
| Drift    | ~67 MNOK    | 72.02 MNOK     | +7.5 % |
| Vedlikehold | ~40 MNOK | 43.55 MNOK    | +8.9 % |
| **TOTALT** | **545.11 MNOK** | **560.64 MNOK** | **+2.85 %** |

Økonomiavd. vedtatt budsjett 2026: ~567 MNOK (BEFS avvik: ~−6.4 MNOK / −1.1 %)

---

## Implementasjonsdetaljer

| Felt | Verdi |
|------|-------|
| `budget.data_source` | `'okonomi_regional_2026'` |
| `budget.year` | `2026` |
| `budget.is_synthetic` | `true` |
| Antall rader | 3 539 |
| Antall eiendommer | 206 |
| Script | `backend/scripts/rebuild_befs_2026_regional.py` |

---

## Verifikasjonsquery

```sql
SELECT
    data_source,
    COUNT(*) AS rader,
    COUNT(DISTINCT property_id) AS eiendommer,
    SUM(amount)::float AS total_nok
FROM budget
WHERE year = 2026 AND data_source = 'okonomi_regional_2026'
GROUP BY data_source;
-- Forventet: 3539 rader, 206 eiendommer, ~560 640 000 NOK
```

---

## Historikk — forkastede metoder

| Versjon | data_source | Metode | Forkastet fordi |
|---------|-------------|--------|-----------------|
| v1 | `holt_winters_2026_xgb70` | Holt-Winters + XGBoost ML | For lite historikk, store feil |
| v2 | `kontant_2025_plus_3.5pct` | Flat 3.5 % prisjustering for alle | Ikke representativ — økonomi bruker ulike rater per region |
| **v3** | `okonomi_regional_2026` | **Regionale vekstrater (gjeldende)** | — |

---

## Kilde og sporbarhet

- **Økonomibudsjett**: lastet opp via `/admin/budsjett-import` → `finance_budget WHERE data_source='finance_dept_2026'`
- **Regnskap 2025**: lastet opp som Agresso kontant-eksport → `finance_budget WHERE data_source='kontant_2025'`
- **Regionkobling**: `koststed_mapping` — vedlikeholdt av BEFS-administrasjon
- **Rebuild-script**: `backend/scripts/rebuild_befs_2026_regional.py` — idempotent, kan kjøres på nytt ved behov
