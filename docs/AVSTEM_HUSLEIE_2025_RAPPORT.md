# Avstemning: Faktisk husleie 2025 – BEFS vs Innkjøpsanalyse-CSV

## Total kost (mars 2025)

**Total kost** = hele blokken «Leie av lokaler og tilknyttede utgifter» fra Innkjøpsanalyse (ca. 504 MNOK 2025). Inkluderer husleie + løpende utgifter (fellesutgifter, strøm, renhold, reparasjon m.m.). Lagres i `property_husleie_csv` og vises som «Total kost 2025» på eiendomssiden og Financials når Innkjøpsanalyse-import er kjørt.

## Husleie-definisjon (korrigert mars 2025)

**Husleie** = kun disse to kategorier fra regnskapet:
- **Leie lokaler andre utleiere** (213,2 MNOK total)
- **Leie lokaler fra Statsbygg** (134,5 MNOK total)

**Ikke** husleie: Leie parkeringsplass, Fellesutgifter, Strøm, Renhold, Reparasjon, Annen kostnad lokaler, etc.

## 1. Oppsummering per region

| Region | CSV (Innkjøpsanalyse) | BEFS (GL) | Differanse |
|--------|------------------------|-----------|------------|
| Midt-Norge | 55,519,441 | 0 | -55,519,441 |
| Nord | 60,901,083 | 0 | -60,901,083 |
| Sør | 65,499,654 | 0 | -65,499,654 |
| Vest | 53,372,725 | 0 | -53,372,725 |
| Øst | 94,805,303 | 0 | -94,805,303 |
| Bufdir | 0 | 0 | +0 |
| **Total** | **330,098,206** | **0** | **-330,098,206** |

## 2. CSV total (fra aggregert fil Lokaler, repar og vedlikehold)

- Leie lokaler andre utleiere: **213 211 028 kr**
- Leie lokaler fra Statsbygg: **134 452 952 kr**
- **Total husleie (referanse): 347 663 980 kr**

> Merk: CSV-filen inneholder flere kategorier (fellesutgifter, reparasjon, etc.). Vi importerer kun *husleie*-kategorier til property_husleie_csv.

**Import 2025-03-10:** 30 rader importert fra Lokaler repar vedlikehold konti (3).csv. Matching forbedret: min_score 0.55, region-sjekk ved mismatch (krever 0.7), logging av matcher med score < 0.7. 68 radetiketter umatchbare (Kontorfaglig enhet, Stab, Regionkontor m.fl.). Backup lagret før re-import.

## 3. Matching radetikett ↔ BEFS department_name

| Radetikett (CSV) | BEFS match | CSV total | BEFS total | Diff |
|------------------|------------|----------|------------|------|

## 4. Radetiketter uten god BEFS-match

- **Regionkontor**: 105,407,217 kr
- **Kontorfaglig enhet**: 19,829,325 kr
- **Trøndelag behandlingssenter for ungdom**: 7,011,381 kr
- **Lågen ungdomshjem**: 6,739,288 kr
- **Grøterød ungdomshjem**: 6,213,901 kr
- **Nye Kvæfjord ungdomssenter**: 6,153,367 kr
- **Røvika Ungdomssenter**: 5,758,743 kr
- **Bergen Akuttsenter Ungdom**: 5,482,271 kr
- **Barkåker ungdomssenter**: 5,235,867 kr
- **Bodø behandlingssenter**: 5,106,608 kr
- **Fosterhjemstjenesten, Bufetat region sør**: 4,985,834 kr
- **Kvammen akuttinstitusjon**: 4,968,096 kr
- **Familievernkontoret for Bergen og omland**: 4,515,730 kr
- **Stab**: 4,472,405 kr
- **Nye Lamo ungdomssenter**: 4,304,481 kr
- **Solbakken Barne- og familiesenter**: 4,205,419 kr
- **Tromsø ungdomssenter**: 4,157,211 kr
- **Agder ungdomssenter**: 4,054,870 kr
- **Alta Ungdomssenter**: 3,744,405 kr
- **Enhet for inntak, Bufetat region sør**: 3,735,131 kr
- **FHT region nord**: 3,590,065 kr
- **Husafjellheimen ungdomsheim**: 3,491,864 kr
- **Region vest senter for foreldre og barn**: 3,487,212 kr
- **Regionale utgifter (regionkontor,fellestjenester)**: 2,994,415 kr
- **Yttrabekken Ungdomshjem**: 2,918,029 kr
- **Thorøya ungdomshjem**: 2,903,823 kr
- **MST region sør**: 2,797,007 kr
- **Klokkerhuset ungdomssenter akutt**: 2,758,874 kr
- **Sollia barne- og ungdomssenter**: 2,688,465 kr
- **Vikhovlia akuttsenter**: 2,626,468 kr
- **Kasa Ungdomssenter**: 2,577,930 kr
- **Telemark barne- og familiesenter**: 2,503,904 kr
- **Sandnes Ungdomssenter**: 2,500,221 kr
- **Stavanger Akuttsenter Ungdom**: 2,449,168 kr
- **Sundstedtråkka ungdomssenter akutt**: 2,382,793 kr
- **Humla Akuttsenter**: 2,352,140 kr
- **Ranheim Vestre**: 2,295,326 kr
- **Viktoria Familiesenter**: 2,180,656 kr
- **Familievernkontorene Drammen-Kongsberg**: 2,140,993 kr
- **Lunde behandlingssenter**: 2,126,809 kr
- **Fosterhjemstjenesten, Bufetat region midt**: 2,104,915 kr
- **Skjoldvegen barnevernsenter**: 2,087,740 kr
- **Agder barne- og familiesenter**: 2,076,761 kr
- **Gilantunet ungdomshjem**: 2,036,347 kr
- **Bjørgvin Ungdomssenter**: 2,033,191 kr
- **Silsand ungdomssenter**: 2,001,746 kr
- **Senter for foreldre og barn Molde**: 1,989,932 kr
- **Enhet for inntak, Bufetat region nord**: 1,956,549 kr
- **Skjerven rusbehandling ungdom**: 1,842,819 kr
- **Tromsø Familievernkontor**: 1,799,077 kr
- ... og 72 flere

## 5. Konklusjon

- CSV husleie (Leie lokaler andre + Statsbygg, kun disse to): **347 663 980 kr** (referanse fra aggregert fil)
- Importert til property_husleie_csv: 74 rader (ca. 319 MNOK fra matchede radetiketter)
- BEFS GL husleie (is_lease_account): **0 kr**
- Differanse: **-347 663 980 kr**

Mulige årsaker til avvik:
- Forskjellig definisjon av husleie (CSV vs GL account_name)
- Transaksjoner uten property_id/department_code i BEFS
- Forskjellig region-mapping (region_name i GL vs property.region)
- Tidsrom/perioder (hele 2025 vs delvis)
