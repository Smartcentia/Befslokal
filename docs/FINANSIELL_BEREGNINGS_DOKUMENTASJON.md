# Finansiell Beregningsdokumentasjon

Dette dokumentet beskriver den matematiske logikken og formlene som brukes i systemet for å beregne finansielle nøkkeltall, budsjetter og risikoanalyser. Dokumentet dekker beregninger som vises på `/financials`, eiendomssidene og i risikoanalysen.

## 1. Grunnlagsdata og Definisjoner

### 1.1 Leieinntekter (Annual Rent)
Beregnes som summen av årlige leieinntekter fra alle **aktive** kontrakter knyttet til en eiendom.

**Formel:**
$$ \text{Total Leie} = \sum_{c \in \text{Contracts}} \text{amount\_per\_year}(c) $$

*   **Filter:** `contract.status == 'active'`
*   **Datakilde:** `contracts`-tabellen.
*   **Logikk:**
    *   Henter `amount_per_year` direkte hvis tilgjengelig.
    *   Alternativt: `monthly_rent * 12`.
    *   Hvis ingen av delene finnes, benyttes `total_per_year`.

### 1.2 Kostnader / Forbruk (Actual Costs)
Summen av alle bokførte kostnader og registrerte utgifter for en gitt periode (vanligvis siste 12 måneder eller kalenderår).

**Formel:**
$$ \text{Total Kostnad} = \sum (\text{Manual Expenses}) + \sum (\text{CSV Spend}) + \text{Total Maintenance} $$

*   **Datakilde:** `property.external_data.financials`
*   **Komponenter:**
    *   **Manual Expenses:** Enkelstående utgifter registrert manuelt på eiendommen.
    *   **CSV Spend:** Utgifter importert og kategorisert fra bank/regnskapsutdrag.
    *   **Maintenance:** Aggregerte vedlikeholdskostnader importert fra forvaltningssystemet.

---

## 2. Kategorisering og Analyse

### 2.1 Leverandørklassifisering
Systemet klassifiserer automatisk utgifter for å skille mellom ren leiebetaling (til gårdeier) og driftskostnader.

*   **Leietaker (Husleie):** Utgifter der kategorien inneholder nøkkelord som:
    *   "leie lokaler", "husleie", "leie av lokaler", "leieavtale"
*   **Løpende Drift (Driftskostnader):** Alle andre kategorier.
    *   *Underkategorier*:
        *   **Strøm og oppvarming**: Kategori inneholder "strøm" eller "oppvarming".
        *   **Fellesutgifter**: Kategori inneholder "fellesutgift".
        *   **Annen kostnad**: Resten.

### 2.2 Leverandørkonsentrasjon (Supplier Concentration)
En risikoindikator som måler hvor stor andel av de totale kostnadene som går til én enkelt leverandør.

**Formel:**
$$ \text{Share \%} = \left( \frac{\text{Største Leverandør Beløp}}{\text{Total Eiendomskostnad}} \right) \times 100 $$

*   **Risikogrenser:**
    *   > 50%: Høy konsentrasjon (potensiell risiko).
    *   Sjekkes også mot antall leverandører (få leverandører øker risikoen).

### 2.3 Prisvariasjon (Price Variation / CV)
Måler inkonsistens i prising fra samme leverandør på tvers av ulike eiendommer.

**Formel (Variasjonskoeffisient - CV):**
$$ CV = \left( \frac{\sigma}{\mu} \right) \times 100 $$

Hvor:
*   $\sigma$ (Standardavvik): Mål på spredning i beløpene fra leverandøren.
*   $\mu$ (Snitt): Gjennomsnittlig beløp per eiendom for denne leverandøren.

---

## 3. Budsjettgenerering (Syntetisk Budsjett)

For eiendommer som mangler offisielle budsjetter i systemet, genererer `BudgetGenerationService` syntetiske budsjetter basert på historiske data eller estimater.

### 3.1 Metode A: Basert på Historisk Regnskap (GL Data)
Brukes når det finnes transaksjoner (GL Transactions) for de siste 12 månedene.

1.  **Gjennomsnitt:** Beregn snittlig månedskostnad ($\text{Avg}$) per kategori.
2.  **Inflasjon:** Juster med KPI (standard 3.5%).
    $$ \text{Base} = \text{Avg} \times (1 + \text{Inflation}) $$
3.  **Varianspåslag:** Legg til et tilfeldig avvik basert på kategoriens usikkerhet:
    *   *Property/Rent*: $\pm 5\%$
    *   *Operations*: $\pm 15\%$
    *   *Investment*: $\pm 30\%$
    *   *Other*: $\pm 20\%$
4.  **Sesongjustering (Operations):**
    *   Vinter (Nov-Feb): $\times 1.2$
    *   Sommer (Jun-Aug): $\times 0.8$

### 3.2 Metode B: Fallback (Estimert fra Leie)
Brukes når ingen historiske data finnes. Baseres på bransjestandard nøkkeltall relatert til årlig leie.

*   **Anslått Eiendomskostnad (Property):** $120\%$ av Årlig Leie.
*   **Anslått Driftskostnad (Operations):** $15\%$ av Årlig Leie.
*   Tallene fordeles over året med samme sesongprofil som over.

---

## 4. Nøkkeltall (KPIer)

### 4.1 Kostnad / Leie Forhold (Cost to Rent Ratio)
Indikerer finansielle bærekraft. Hvor mye koster eiendommen i drift sammenlignet med husleien?

**Formel:**
$$ \text{Ratio} = \frac{\text{Total Costs}}{\text{Total Rent}} $$

*   **Tolkning:**
    *   $< 0.8$: Akseptabelt nivå.
    *   $> 0.8$: **Obs!** (Advarsel).
    *   $> 1.0$: **Kritisk** (Utgifter overstiger leieinntekter).

### 4.2 Kostnad per Kvadratmeter
Standardisert kostnadsmål.

**Formel:**
$$ \text{NOK/m}^2 = \frac{\text{Total Costs}}{\text{Total Area}} $$

*   Krever at `total_area` er definert (> 0).

### 4.3 Prioriteringsindeks (Priority Index)
Brukes for å rangere eiendommer etter viktighet i risikoanalysen.

**Formel:**
$$ \text{Index} = \text{Risk Score} \times (\text{Total Costs} + \text{Total Rent}) $$

*   Kombinerer risiko med økonomisk omfang. En stor eiendom med moderat risiko kan rangeres over en liten eiendom med høy risiko.

---

## 5. Risikoanalyse (Økonomisk)

Økonomisk risiko er en delkomponent av den totale risikoscoren (0-100).

**Beregning:**
Den baseres primært på **Cost/Rent Ratio**:
1.  Basis: 0 poeng.
2.  Hvis **Ratio > 1.0**: $+40$ poeng.
3.  Hvis **Ratio > 0.8** (men $\le 1.0$): $+20$ poeng.
4.  Budsjettavvik (hvis tilgjengelig): Store negative avvik øker scoren (implementeres løpende).


Denne modellen sikrer at eiendommer med usunn økonomi flagges automatisk for oppfølging.

---

## 6. Avanserte Porteføljeanalyser

Systemet kjører en rekke avanserte analyser for å identifisere mønstre på tvers av hele eiendomsporteføljen. Disse beregningene kjøres nattlig eller ved behov via `/financials`.

### 6.1 Geografiske Mønstre (Regional Patterns)
Sammenligner kostnadsnivået mellom ulike regioner og identifiserer eiendommer som avviker fra regionssnittet.

*   **Regionalt Snitt:** Gjennomsnittlig kostnad for alle eiendommer i en region.
*   **Avvik (Deviation):**
    $$ \text{Deviation \%} = \left( \frac{\text{Property Cost} - \text{Regional Avg}}{\text{Regional Avg}} \right) \times 100 $$
*   **Formål:** Identifisere om en eiendom er dyr fordi den ligger i en dyr region, eller om den er dyr *relativt* til naboene.

### 6.2 Tidsserieanalyse & Sesongmønstre
Analyserer kostnader over tid for å finne sesongvariasjoner.

*   **Sesongindeks (Vinter/Sommer):**
    *   *Vinter:* Sum kostnader i Nov, Des, Jan, Feb.
    *   *Sommer:* Sum kostnader i Jun, Jul, Aug.
*   **Handling:** Hvis Vinter-kostnader er unormalt mye høyere enn Sommer (> 50% forskjell), kan det indikere dårlig isolasjon eller ineffektiv oppvarming.

### 6.3 Kostnads-Skalering (Scaling Patterns)
Analyserer hvordan kostnader skalerer med størrelsen på bygget.

*   **Skaleringseffekt:** Plotter `Total Cost` mot `Total Area`.
*   **Outlier Deteksjon:** Bruker standardavvik (Z-score) på `Cost per Sqm` for å finne eiendommer som ligger signifikant over trendlinjen.
    $$ Z = \frac{x - \mu}{\sigma} $$
    *   Hvor $x$ er eiendommens kvm-pris, $\mu$ er snittet for porteføljen.
    *   Eiendommer med $Z > 2$ flagges som "dyre outliers".

### 6.4 Leverandøranalyse (Supplier Intelligence)

*   **Prisvariasjon (CV):** (Beskrevet i 2.3) - Avslører om vi betaler ulik pris for samme tjeneste.
*   **Leverandør-Overlapp (Jaccard Index):** Måler hvor like leverandørlistene er mellom to eiendommer.
    $$ J(A,B) = \frac{|A \cap B|}{|A \cup B|} $$
    *   Hvor $A$ og $B$ er settene med leverandører for eiendom A og B.
    *   Høy overlapp (> 30%) indikerer mulighet for sammenslåing av avtaler.

### 6.5 Cluster-analyse (AI/ML)
Systemet bruker *k-means clustering* for å gruppere eiendommer som har lignende kostnadsprofil ("Cost DNA").

*   **Vektorer:** Hver eiendom representeres av andelen kostnader i kategoriene `[Property, Operations, Investment, Other]`.
*   **Grupper:**
    1.  **Driftsintensive:** Høy andel "Operations" (typisk eldre bygg).
    2.  **Husleietunge:** Høy andel "Property" (leide lokaler).
    3.  **Investeringsfokus:** Høy andel "Investment" (under oppussing).
    4.  **Balanserte:** Jevn fordeling.


### 6.6 Datakvalitet (Missing Data Patterns)
Analyserer "hull" i datagrunnlaget for å veilede datavask.

*   **High Rent / No Costs:** Eiendommer med leieinntekter men null registrerte kostnader (sannsynligvis manglende bilag).
*   **Missing Area:** Kostnader registrert, men areal mangler (umuliggjør kvm-analyse).

---

## 7. Bygnings- og Bruksanalyse

Kobler finansielle data med eiendommens fysiske egenskaper for å finne drivere av høye kostnader.

### 7.1 Bygningsalder (Building Age)
Grupperer eiendommer basert på alder for å analysere vedlikeholdsbehov.

*   **Kategorier:**
    *   `<10 år`: Nybygg (forventet lave kostnader).
    *   `10-30 år`: Middels alder (begynner å kreve vedlikehold).
    *   `30-50 år`: Renoveringsobjekter.
    *   `>50 år`: Eldre bygg (ofte høyere driftskostnader).
*   **Formål:** Benchmarking av kostnader innenfor samme alderssegment.

### 7.2 Energimerking (Energy Label)
Analyserer sammenheng mellom energimerking (A-G) og faktiske driftskostnader.

*   **Formål:** Verifisere om investeringer i energieffektivisering gir forventet utslag i lavere strøm/oppvarmingskostnader.

### 7.3 Brukstype (Usage Type)
Grupperer eiendommer etter primærbruk (f.eks. Skole, Sykehjem, Kontor) for mer relevant benchmarking.

*   **Datakilde:** `units.usage_type` eller `property.usage`.

---

## 8. Geografisk Detaljanalyse

### 8.1 Kommuneanalyse
Aggregerer kostnader per kommune for å se hvor de største utgiftspostene ligger geografisk, uavhengig av regioninndeling.

### 8.2 Senteranalyse
For porteføljer organisert i sentre/avdelinger, analyseres kostnadsfordelingen per senter-ID. Dette muliggjør internfakturering og kostnadsallokering.

---

## 9. Operasjonell Effektivitet

### 9.1 Transaksjonstetthet (Transaction Density)
Analyserer fakturamengde kontra totalbeløp.

*   **Høy tetthet:** Mange små fakturaer per eiendom (ineffektiv administrasjon).
*   **Lav tetthet:** Få store fakturaer.
*   **Kostnad per Transaksjon (Avg):** $\frac{\text{Total Costs}}{\text{Num Expenses}}$.

### 9.2 Kategori-Diversifikasjon
Måler bredden i kostnadsbildet.

*   **Single Category:** Eiendommer som kun har kostnader i én kategori (feks bare Strøm, men mangler Renhold). Kan indikere manglende kostnadsføring.
*   **Many Categories:** Komplekse eiendommer med kostnader i $\ge 8$ unike kategorier.

### 9.3 Kategori-Kombinasjoner (Bundles)
Finner kategorier som ofte opptrer sammen (f.eks. "Fellesutgifter" + "Strøm").
*   **Bruk:** Hvis en eiendom har den ene men mangler den andre, kan det indikere en feil eller et avvik.

---

## 10. Detaljert Kostnadsanalyse

### 10.1 Kostnad per kvm per Kategori
Bryter ned total kvm-kostnad i komponenter for dypere innsikt.

*   **Eksempel:** En eiendom kan ha normal totalkostnad, men ekstremt høy kostnad for "Renhold" per kvm sammenlignet med snittet.

### 10.2 Budsjettvarians (Budget Variance)
Detaljert avviksanalyse mellom budsjett og regnskap (GL).

*   **Formel:**
    $$ \text{Variance \%} = \left( \frac{\text{Budget} - \text{Actual}}{\text{Budget}} \right) \times 100 $$
*   **Ranking:** Sorterer eiendommer etter absolutt avvik i kroner for å prioritere de største budsjettsprekkene.


