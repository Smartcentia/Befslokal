# Rapport: Husleie fra Innkjøpsanalyse

**År:** 2025

## 1. Oppsummering

| Kilde | Beløp | Beskrivelse |
|-------|-------|-------------|
| property_husleie_csv (matchede eiendommer) | 105.3 MNOK | 38 eiendommer med direkte match |
| total_kost_per_region_2025.json | 504.4 MNOK | Full oversikt (alle radetiketter inkl. Bufdir, Regionkontor) |
| eiendom_avdeling_mapping.json | — | 110 avdelinger mappet til eiendommer |

## 2. Eiendommer med Innkjøpsanalyse-husleie

Disse eiendommer har fått husleie fra Innkjøpsanalyse-CSV (lagret i property_husleie_csv):

| Eiendom | Region | Total (NOK) |
|---------|--------|-------------|
| Nye Kvæfjord ungdomssenter avdeling 3 | Nord | 8,817,720 |
| Røvika ungdomssenter Skogly | Nord | 8,383,959 |
| Bodø behandlingssenter Landegode | Nord | 5,787,688 |
| Tromsø Ungdomssenter | Nord | 5,753,946 |
| Lamo Ungdomssenter | Nord | 5,295,276 |
| Alta Ungdomssenter | Nord | 5,271,889 |
| Solbakken barne- og familiesenter | Nord | 4,934,743 |
| Stavanger akuttsenter - Madla | Vest | 4,814,227 |
| Sandnes Ungdomssenter, Boligen | Vest | 4,156,554 |
| Klokkerhuset ungdomssenter akutt, avd. beredskapsh | Sør | 3,801,091 |
| Regionkontoret region sør | Sør | 3,666,331 |
| Viktoria familiesenter | Midt-Norge | 3,596,743 |
| Sollia barne- og ungdomssenter | Nord | 3,523,742 |
| Vikhovlia akuttsenter | Midt-Norge | 3,513,721 |
| Lunde behandlingssenter | Sør | 3,265,189 |
| Senter for familie og barn, Molde | Midt-Norge | 3,178,049 |
| Ranheim Vestre | Midt-Norge | 2,890,900 |
| Stavanger ungdomssenter Lindøy | Vest | 2,802,733 |
| Humla Akuttsenter | Midt-Norge | 2,759,716 |
| Karienborg ungdomsheim | Midt-Norge | 2,707,858 |
| Gilantunet ungdomshjem | Midt | 2,590,886 |
| Silsand ungdomssenter miljøavdeling | Nord | 2,241,920 |
| Sogn og Fjordane ungdomssenter avdeling Bregnetune | Vest | 1,960,831 |
| Familievernkontoret i Molde | Midt-Norge | 1,534,003 |
| Clausenengen ungdomshjem | Midt-Norge | 1,533,396 |
| Bodø Familievernkontor | Nord | 1,454,202 |
| Bufetats behandlingssenter Akershus_Østfold, avd Ø | Øst | 1,076,234 |
| Eikelund ungdomssenter | Vest | 746,715 |
| Hedmark ungdoms- og familiesenter - akutt, avd Sta | Øst | 699,274 |
| Kirkenær barnevern- og omsorgssenter Avdeling Frig | Øst | 603,326 |
| Østfold ungdoms- og familiesenter - omsorg avdelin | Øst | 602,668 |
| Borg barne og familiesenter, avlaster for beredska | Øst | 329,669 |
| Jong ungdoms- og familiesenter, avd Kollen | Øst | 282,259 |
| Lierfoss ungdoms- og familiesenter - omsorg Furuli | Øst | 240,524 |
| Familievernkontoret Innlandet Øst - Hamar | Øst | 205,374 |
| Familievernkontoret Oslo Nord | Øst | 154,334 |
| Driftsavdeling region vest | Vest | 77,285 |
| Akershus ungdoms- og familiesenter - akutt, avd So | Øst | 2,726 |

## 3. Total kost per region (fra JSON)

| Region | Beløp (NOK) |
|--------|--------------|
| Øst | 135,333,429 |
| Sør | 98,714,321 |
| Nord | 80,961,639 |
| Midt-Norge | 79,627,503 |
| Vest | 78,175,049 |
| Bufdir | 31,636,306 |
| **Total** | **504,448,247** |

## 4. Dataflyt

```
Innkjøpsanalyse-CSV
       │
       ├── match radetikett → eiendom (fuzzy + eiendom_avdeling_mapping)
       │         └── property_husleie_csv (property_id, year, region, amount)
       │
       └── alle radetiketter (inkl. subtotaler)
                 └── total_kost_per_region_{year}.json (by_category, by_region_totals)
```

**API-endepunkter:**
- `GET /api/v1/properties/innkjoepsanalyse-husleie?year={year}` → by_property (fra property_husleie_csv)
- `GET /api/v1/properties/total-kost-per-region?year={year}` → by_category (fra JSON)

**Bruk i frontend:**
- Financials: Total kost 2025 bruker total_kost_per_region når tilgjengelig (504 MNOK)
- Eiendomsside: Total kost 2025 bruker innkjøpsanalyse.by_property[property_id].aggregert
- Budsjett 2026: Eiendommer med property_husleie_csv får eksakte beløp; resten fordeles fra regionale restbeløp
