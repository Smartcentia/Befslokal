# Metodikk for risikovurdering og kostnadsanalyse i BEFS

**Dokumenttype:** Vitenskapelig/teknisk metodikk  
**Versjon:** 1.0  
**Sist oppdatert:** Februar 2025

---

## 1. Sammendrag

BEFS (Bufetat Eiendomsforvaltningssystem) bruker tre hovedmodeller for å støtte beslutninger om eiendomsporteføljen: (1) en risikoscore basert på proxy-indikatorer for sannsynlighet og konsekvens, (2) en kostnadsanalyse som sammenligner utgifter med årlig husleie, og (3) en budsjettmodell som genererer syntetiske budsjetter fra historiske kostnader og brukes til variansanalyse. Dokumentet beskriver de matematiske formuleringene, antakelsene og begrensningene.

---

## 2. Risikovurdering

### 2.1 Modellidé

Risikoscoren bygger på den klassiske modellen

$$R \approx P \times C$$

der \(R\) er risiko, \(P\) er sannsynlighet for hendelse, og \(C\) er konsekvens. I BEFS implementeres dette som en **poengscore** (0–100) for å rangere eiendommer etter oppfølgingsbehov.

### 2.2 Viktig presisering: Proxy-indikatorer

**P og C representerer her proxy-indikatorer, ikke faktiske sannsynligheter eller kroner.**

- \(P\) er ikke en estimert sannsynlighet \(P(\text{hendelse}) \in [0,1]\).
- \(C\) er ikke forventet tap i kroner (E[skade]).
- \(R\) er derfor **ikke** «ekte» risiko i form av forventet tap, men en **relativ prioriteringsindikator**.

Scoren skal brukes til å rangere eiendommer etter oppfølgingsbehov, ikke som absolutt risikomål. Tolkning: Høyere score = større behov for oppfølging.

### 2.2.1 Bruk som beslutningsmodell

Risikoscoren brukes som **prioriteringsparameter** for ressursallokering på tvers av budsjettkategorier (husleie/eiendom, drift, investering og reserve). Den representerer ikke forventet økonomisk tap, men styrer **rekkefølge og tiltaksbehov**. Tolkning: «Dette er hvor midler bør prioriteres først», ikke «dette er forventet tap».

### 2.3 Komponenter i risikoscoren

Risikoscoren består av to deler:

#### 2.3.1 Ekstern risiko (external_risk_score)

Summerer bidrag fra:

| Faktor | Bidrag | Betingelse |
|--------|--------|-------------|
| Bygningsalder | \(0{,}5 \cdot \max(0, \text{alder})\) | Alder = nåværende år − byggeår |
| Stort areal | +10 | \(\text{sqm} > 10\,000\) |
| Nærhet til vannvei (NVE) | +15 | Nærmeste NVE-stasjon \(< 1\,\text{km}\) |
| Aktivt flomvarsel | +25 | NVE flomvarsel nivå \(> 1\) |

Ekstern risiko capes til 100: \(\text{external\_risk\_score} = \min(100, \lfloor \text{sum} \rfloor)\).

#### 2.3.2 Operasjonell risiko (deviation_score)

Basert på åpne avvik i internkontroll:

- 10 poeng per åpent avvik
- Ekstra 10 poeng per avvik i tiltaksfase (manglende tiltak)

Hovedscoren (final_risk_score) er kun avviksbasert og capes til 100.

#### 2.3.3 Statuskategorier

| Score | Status |
|-------|--------|
| \(> 75\) | Kritisk |
| \(> 40\) | Høy |
| \(> 0\) | Moderat |
| \(0\) | Lav |

### 2.4 Eksterne datakilder (NVE)

Ekstern risiko bruker data fra NVE (Norges vassdrags- og energidirektorat):

- **HydAPI:** Nærliggende hydrologiske stasjoner (radius 10 km). Avstand beregnes med Haversine-formelen.
- **Flomvarsel API:** Aktive varsler per fylke (fylkesnummer fra Kartverket).

Nærhet til vannvei indikeres ved at nærmeste stasjon er under 1 km. Aktivt flomvarsel (nivå \(> 1\)) gir økt ekstern risiko.

---

## 3. Kostnadsanalyse

### 3.1 Formål

Kostnadsanalysen sammenligner eiendommers utgifter med årlig husleie for å identifisere avvik fra forventede nivåer. Den produserer ratioer og en kvalitativ vurdering (NORMAL, MODERAT, HØY, KRITISK).

### 3.2 Matematisk formulering

For hver kostnadskategori \(k\) og for totalen:

$$\text{ratio}_k = \frac{\text{kategori\_sum}_k}{\text{annual\_rent}}$$

$$\text{total\_ratio} = \frac{\text{total\_costs}}{\text{annual\_rent}}$$

Prosentvis: \((\text{ratio} \cdot 100)\,\%\).

### 3.3 Håndtering av annual_rent = 0

Ved manglende husleiedata (\(\text{annual\_rent} = 0\) eller null) settes alle ratioer til 0:

$$\text{ratio}_k = 0 \quad \text{når} \quad \text{annual\_rent} \leq 0$$

Dette unngår deling på null og meningsløse ratioer. Vurderingsgrenser (KRITISK/HØY/MODERAT) gis da ikke; systemet returnerer «UKJENT: Mangler husleiedata for sammenligning».

### 3.4 Kostnadskategorier og forventede forhold

| Kategori | Eksempler | Min | Maks | Typisk |
|----------|-----------|-----|------|--------|
| property | Husleie, fellesutgifter, parkering | 80 % | 200 % | 120 % |
| operations | Strøm, renhold, vakthold, vedlikehold | 5 % | 50 % | 15 % |
| investment | Inventar > 50k, oppgradering, ombygging | 0 % | 100 % | 10 % |

### 3.5 Vurderingsgrenser (total_ratio)

| total_ratio | Vurdering |
|-------------|-----------|
| \(> 3{,}0\) | KRITISK |
| \(> 2{,}0\) | HØY |
| \(> 1{,}5\) | MODERAT |
| \(\leq 1{,}5\) | NORMAL |

**Forutsetning:** Tersklene gir kun mening når \(\text{total\_costs}\) og \(\text{annual\_rent}\) er **sammenlignbare størrelser** (begge per år).

### 3.6 Caveat: Årlighet

\(\text{total\_costs}\) er summen av **alle** poster i \(\text{manual\_expenses}\) uten årfiltrering. \(\text{annual\_rent}\) er årlig leie. Hvis \(\text{manual\_expenses}\) inneholder utgifter fra flere år, blir \(\text{total\_costs}\) flerårig, og ratioene blir **systematisk for høye** uten at det nødvendigvis er «kritisk». Anbefaling: Filtrer utgifter på år (f.eks. siste 12 måneder) før ratio-beregning for å sikre sammenlignbarhet.

---

## 4. Budsjett

### 4.1 Formål

BEFS genererer **syntetiske budsjetter** siden budsjettdata ofte mangler i systemet. Budsjettet brukes til variansanalyse (budsjett vs. faktisk) og som referanse for kostnadsstyring. Budsjettet lagres per eiendom, år og måned i tabellen `budget` (property_id, year, month, category, amount).

### 4.2 Genereringsmetoder

Det finnes to hovedmetoder:

#### 4.2.1 Fra GL-transaksjoner (historiske kostnader)

Når `gl_transactions` inneholder faktiske kostnader fra siste 12 måneder:

1. **Gjennomsnitt per kategori:** \(\bar{x}_k = \text{AVG}(\text{amount})\) for kategori \(k\)
2. **Inflasjonsjustering (KPI):** \(\text{base}_k = \bar{x}_k \cdot (1 + r)\) der \(r\) er standard 3,5 % (SSB-estimat for Norge)
3. **Varians per kategori:** \(\text{budsjett}_k = \text{base}_k + \text{base}_k \cdot \sigma_k \cdot U(-1, 1)\) der \(\sigma_k\) er planleggingsusikkerhet (tabell nedenfor)
4. **Sesongfaktor:** Månedlig budsjett = (årlig budsjett / 12) × sesongfaktor(month, category)

**Kategori-varians (planleggingsusikkerhet):**

| Kategori | \(\sigma_k\) | Begrunnelse |
|----------|--------------|-------------|
| property | 5 % | Husleie er forutsigbar |
| operations | 15 % | Strøm/varme varierer |
| investment | 30 % | Kapitalprosjekter usikre |
| other | 20 % | Diverse |

**Sesongfaktor (kun operations):**
- Vinter (nov–feb): 1,2 (høyere oppvarmingskostnader)
- Sommer (jun–aug): 0,8 (lavere)
- Øvrige måneder: 1,0

#### 4.2.2 Fra forbruk (manual_expenses)

Når GL-transaksjoner mangler, brukes `manual_expenses` fra `external_data.financials`:

1. **Kategorisering:** Samme `EXPENSE_CATEGORY_MAP` som kostnadsanalysen
2. **Årlig budsjett per kategori:** \(\text{budsjett}_k = \text{kategori\_sum}_k \cdot U(1 - v, 1 + v)\) der \(v\) er varians (standard ±20 %)
3. **Fordeling:** Månedlig = (årlig / 12) × sesongfaktor

**Merk:** `kategori_sum` her er summen av alle manual_expenses i kategorien (uten årfiltrering). Samme caveat som kostnadsanalyse: flerårige utgifter gir budsjett som ikke nødvendigvis er sammenlignbart med ett års faktisk.

### 4.3 Fallback ved manglende data

Når verken GL-transaksjoner eller manual_expenses finnes:

1. **Hent årlig husleie** fra aktive kontrakter
2. Ved \(\text{annual\_rent} = 0\): bruk standard 1,2 M NOK/år
3. **Typiske forhold:** Eiendomskostnader ≈ husleie × (1 + KPI), Drift ≈ 15 % av husleie × (1 + KPI)

### 4.4 Variansanalyse (budsjett vs. faktisk)

$$\text{varians} = \text{budsjett} - \text{faktisk}$$

$$\text{varians\_pct} = \frac{\text{varians}}{\text{budsjett}} \cdot 100 \quad \text{når} \quad \text{budsjett} \neq 0$$

For **kostnader** betyr positiv varians at faktisk er under budsjett (gunstig). Variansen beregnes per kategori og aggregeres for måned, kvartal eller YTD.

### 4.5 Antakelser og begrensninger

- Budsjettet er **syntetisk**; det er ikke godkjent budsjett fra budsjettprosessen.
- Inflasjonsraten (3,5 %) er et standardestimat; faktisk KPI kan avvike.
- Varians (±20 % fra forbruk, eller \(\sigma_k\) fra GL) er stokastisk; gjentatt generering gir ulike verdier.
- Sesongfaktoren er heuristisk (vinter/sommer) og kan avvike for enkelte eiendommer.

---

## 5. Antakelser og begrensninger (samlet)

### 5.1 Risikovurdering

- Scoren er en **indikator**, ikke et estimat av forventet tap.
- Proxy-indikatorer (NVE-nærhet, flomvarsel, avvik) er ikke kalibrert mot historisk tap.
- Vekting (f.eks. +15 for NVE-nærhet, +25 for flomvarsel) er heuristisk.

### 5.2 Kostnadsanalyse

- Ratioer krever \(\text{annual\_rent} > 0\); ved null returneres 0 og ingen vurdering.
- \(\text{total\_costs}\) kan være flerårig; tersklene forutsetter årlige tall.
- Forventede forhold (EXPECTED_RATIOS) er basert på bransjestandard og kan avvike for spesialtilfeller.

### 5.3 Budsjett

- Budsjettet er syntetisk, ikke godkjent budsjett.
- Inflasjonsrate og varians er estimater; stokastisk varians gir ulike verdier ved gjentatt kjøring.
- Sesongfaktor er heuristisk.

---

## 6. Prioriteringsindeks (beslutningsmodell)

Risikoscoren kobles til budsjett og kostnader via en **prioriteringsindeks** som styrer hvor midler bør allokeres:

$$\text{Prioritet} = R_{\text{score}} \times \text{Årskostnad} \times \text{Kritikalitetsfaktor}$$

- \(R_{\text{score}}\): Risikoscore (0–100)
- Årskostnad: `annual_rent` + `total_costs` (husleie + bokførte utgifter)
- Kritikalitetsfaktor: Standard 1,0; kan justeres for eiendomstype (f.eks. barnevern)

### 6.1 Reservefaktor (risikotier)

Reservefaktoren brukes til dimensjonering av buffer og scenario-budsjettering:

| Risikotier | Reservefaktor |
|------------|---------------|
| Topp 10 % risiko | 1,5 |
| Midtsjikt | 1,0 |
| Lav risiko (nederste 50 %) | 0,5 |

### 6.2 Styringsklasser

Kostnadskategoriene er mappet til styringsklasser:

| Klasse | Kostnadskategori | Bruk |
|--------|------------------|------|
| A – Husleie/eiendom | property | Baseline, eksponeringsstørrelse |
| B – Drift (OPEX) | operations | Løpende drift, forebyggende tiltak |
| C – Investeringer (CAPEX) | investment | Tiltaksprioritering, investeringsrekkefølge |
| D – Uforutsette | other | Reserve, buffer, stresstest |

---

## 7. Referanser og datakilder

- NVE HydAPI: https://hydapi.nve.no
- NVE Flomvarsling: https://api01.nve.no
- Kartverket (geokoding, fylkesnummer): https://www.geonorge.no
- BEFS teknisk dokumentasjon: `docs/technical.md`
- Budsjettgenerering: `backend/app/services/budget_generation_service.py`
- Variansanalyse: `backend/app/services/variance_service.py`

---

*Dokumentet beskriver den implementerte metodikken i BEFS. Endringer i modellene dokumenteres her.*
