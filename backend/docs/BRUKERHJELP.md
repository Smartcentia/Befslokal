# Brukerhjelp for BEFS / KNOWME

**Velkommen til din nye hverdag!**
Denne guiden hjelper deg å komme i gang med BEFS (Bufetat Eiendomsforvaltningssystem) og din nye digitale assistent, **KI-Kollega**.

---

## KI-Kollega: Din nye superkraft

Glem kompliserte menyer og vanskelige søkefiltre. Med **KI-Kollega** kan du snakke med systemet på vanlig norsk.

### KI-Kollega: Slik fungerer det

1. Klikk på chat-boblen nede til høyre.
2. Still et spørsmål, akkurat som du ville spurt en kollega.
3. Få svar basert på **faktiske data** i systemet.

### Hva kan jeg spørre om?

* **Fakta:** "Hvor mange kvadratmeter leier vi i Region Øst?"
* **Økonomi:** "Hva er totale strømkostnader for Storgata 12 hittil i år?"
* **Søk:** "Finn alle kontrakter som går ut de neste 6 månedene."
* **Analyse:** "Er det noen eiendommer som skiller seg ut negativt på vedlikeholdskostnader?"
* **SSB/Statistikk:** "Hva er KPI nå?" · "Sammenlign våre kostnader med KPI de siste 5 årene" · "Hva sier SSB om leieprisutvikling?"
* **Handlinger:** "Kan du opprette en Jira-sak på at ventilasjonen er dårlig på kontoret i Bodø?" eller "Send en e-post til vaktmester om feil."

### Utføre handlinger (Handlinger på dine vegne)

KI Kollega kan nå **utføre handlinger** i systemet for deg, som for eksempel å opprette saker (via Jira) eller sende beskjeder.
For din sikkerhet vil KI Kollega **aldri** utføre en handling uten din godkjenning:
1. Du ber om en handling (f.eks. "Lag et avvik på...").
2. KI Kollega forbereder oppgaven og presenterer et **Godkjenningskort** i chatten.
3. Du kan lese over detaljene for handlingen og velge **Godkjenn og Utfør** eller **Avvis**.
4. Først når du har trykket Godkjenn, vil systemet gjennomføre oppgaven.

### Skriv som du vil – KI Kollega forstår

Du trenger ikke skrive helt presist. KI Kollega tolker vanlige varianter og forkortelser:

* **Forkortelser:** «fvk» eller «FVK» = familievernkontor. «BUP» og «barnevern» gjenkjennes.
* **Synonymer:** «leietakere» = «parter». «billigste per kvm» = «lavest kostnad per kvm». «kvm» = «kvadratmeter».
* **Ufullstendige spørsmål:** «hvilke er familievern» tolkes som «hvilke eiendommer er familievern».
* **Små skrivefeil:** Vanlige feil (f.eks. «eiendomer» i stedet for «eiendommer») rettes automatisk.

Skriv på vanlig norsk – KI Kollega finner ut hva du mener.

### Kontekst – Den skjønner hvor du er

Hvis du står inne på siden for en spesifikk eiendom, trenger du ikke gjenta navnet på eiendommen.

* *Deg:* "Hvem er vaktmester her?"
* *KI-Kollega:* "Vaktmester på **Storgata 12** er Ola Nordmann..."

### Hvordan KI-Kollega fungerer

KI-Kollega bruker en **samlet modus** som automatisk velger riktige verktøy for spørsmålet ditt. Den kan søke i dokumenter, slå opp i Lovdata, kjøre SQL-analyse mot databasen og hente informasjon om eiendommer, kontrakter og parter. Du trenger ikke velge modus – systemet finner ut hva som trengs.

### Klikkbare lenker i svarene

KI-Kollega gir lenker til **alt informasjon** den finner:

* **Eiendommer, kontrakter og parter:** Klikk for å gå direkte til den aktuelle siden i BEFS – du trenger ikke søke manuelt.
* **Dokumenter:** Lenker til tilhørende kontrakt eller eiendom (der informasjonen ble funnet).
* **Lovdata:** Lenker til lovdata.no for lover og forskrifter.
* **Web-kilder:** Lenker til eksterne nettsteder som ble brukt i svaret.

Under hvert svar vises en **Kilder**-seksjon med opptil 8 lenker. Bruk dem for å verifisere informasjonen eller gå dypere.

---

## Navigasjon og hovedsider

**Venstremeny** er delt i blokker:

* **HOVEDMENY:** Oversikt (dashboard), Innboks, Eiendommer, Kontrakter, Leietakere — samt **Admin** og undermenyer for administratorer.
* **DRIFT & VEDLIKEHOLD:** Sjekklister, Avvikshåndtering, Aktivitetshub, Kalender, Økonomi, SRS-rapport, Anleggsregister, Prediksjon 2027, Eiendomskostnader 2025, Analyse & Innsikt, Risikoanalyse, BUP-lokasjoner, Lovdata-søk, Media Overvåkning (admin).
* **DATA & STATISTIKK:** SSB Statistikk, Barnevern, Institusjoner.
* **APP:** Innstillinger, Hjelp & Dokumentasjon (`/help`).
* **INTEGRASJONER:** Jira (`/jira`).

**Merk:** Menypunktet «Oversikt» åpner **dashboard** (`/dashboard`). Siden **Full porteføljeliste** med drilldown av eiendommer, enheter, kontrakter og leietakere samt prognoseseksjon ligger på **`/oversikt`** (egen sti; nyttig for komplett dataoversikt).

**Andre nyttige stier:** Intern kontroll og outlier-gjennomgang **`/kontroll-2027`**, Agresso CSV-validering **`/agresso-csv`**, KI Research Lab **`/lab`**, dataordliste **`/governance/glossary`**.

---

## Hovedfunksjoner i BEFS

### 1. Dashboard

Din startside (menypunktet «Oversikt», sti `/dashboard`). Her får du en umiddelbar oversikt over porteføljen, kritiske varsler (som kontrakter som løper ut) og nøkkeltall.

**Dashboard-varianter:** Klikk på dashboard-ikonet (med pil) i headeren for å velge mellom ulike visninger: Standard, Cyberpunk, Minimalist, Terminal eller Nordic. Velg den som passer deg best.

**Standarddashboard (ikke eiendomsforvalter-rolle):** Viser blant annet **kart** over porteføljen, **Nye oppdateringer** (siste aktivitet og kontrakter som utløper innen 90 dager), **Topp 5 leietakere**, **Activity Wheel** (årshjul for planlagte HMS- og internkontroll-aktiviteter) og panelet **Kritiske avvik** (åpne saker med prioritet høy/kritisk, med lenke videre til saken). Brukere med rolle **Eiendomsforvalter** får en egen **Mine eiendommer**-visning i stedet for standarddashboard.

**Innboks** (`/innboks`, også i hovedmenyen) samler **varsler** fra internkontroll (f.eks. ML-anomalier, saker). Klikk på et varsel for å markere det som lest og gå til relatert eiendom eller sak.

### 2. Eiendommer, Kontrakter og Leietakere



#### Topp 10 Leietakere (Dashboard)
På dashboardet finner du en oversikt over de 10 største leietakerne sortert etter årlig omsetning (leieinntekter). Listen viser leietakers navn, total årlig leie, antall kontrakter og en visuell indikator på hvor stor andel de utgjør av den største leietakeren.


Her ligger "fasiten" (Stamdata).

* **Eiendomsregisteret:** Oversikt over alle lokasjoner.
* **Kontrakter:** Digitale kopier av alle leieavtaler, koblet direkte mot eiendommen. Vi passer på utløpsdatoer for deg.
* **Leietakere:** Oversikt over leietakere. For detaljert informasjon om en bedrift (BRREG-data, risikovurdering, firmaoppsummering) – gå til **Parter**-siden.

### 3. Økonomi og Analyse

Vi kobler regnskap (hva vi har betalt) med kontrakt (hva vi skal betale).

* **Kostnadsoversikt:** Se hva pengene faktisk går til (Strøm, Renhold, Leie).
* **Avvik:** Systemet varsler hvis fakturaene ikke stemmer med budsjett eller kontrakt.
* **Leverandørstatistikk:** Aggregert oversikt over alle leverandører og kostnadsmønstre på tvers av eiendommer.
* **Regional Oversikt:** Finansiell sammenligning per Bufetat-region.

#### Prediksjon 2027 og interaktiv budsjettjustering

Siden **Prediksjon 2027** (i venstremenyen) viser maskinlæringsbaserte kostnadsestimater for alle 190 eiendommer i porteføljen:

* **Total eiendomsdrift 2027:** ~615 MNOK (Holt-Winters-algoritme, GL-historikk 2021–2025)
* **Lønnskostnader 2027:** ~645 MNOK (separat Holt-Winters på lønnsdata)
* **Per region og kategori:** Drift, Gjennomstrømning og Investering

**Interaktiv budsjettjustering** (knappen "Juster budsjett" øverst på prediksjonssiden):

Åpner en Excel-lignende side der du kan endre tall og se alle avhengige celler oppdateres øyeblikkelig:
1. **Generell kostnadsvekst** — slider + tekstfelt (standard 7,5 %)
2. **Lønnsøkning** — utover Holt-Winters-prediksjon (standard 4,5 %)
3. **Region-faktorer** — juster én region opp/ned uten å påvirke de andre
4. Alle kolonner for "Justert 2027" oppdateres live i tabellene for region, kategori og topp 20 eiendommer
5. **Last ned Excel** — genererer et Excel-ark med de samme formlene (5 ark)

> Du trenger ikke lagre — justeringene lever i nettleseren og brukes kun til planlegging og scenariokjøring.

### 4. Ekstern Risiko (Naturfare)

Vi sjekker automatisk adressen mot NVE sine kart.

* **Faresoner:** Se umiddelbart om et bygg ligger i flom- eller skredutsatt område.
* **Beredskap:** Hjelper deg å ta gode valg *før* uhellet er ute.

### 5. HMS og Kalender

Internkontroll satt i system.

* **Årshjul:** Oppgaver kommer automatisk i kalenderen din basert på hva slags bygg det er (f.eks. Institusjon vs. Kontor).
* **Avvik:** Avvikelse fra krav eller plan (f.eks. manglende dokumentasjon, forfalt inspeksjon, HMS-brudd). Overvåkes via sjekklister og internkontroll. Meld inn avvik, og systemet følger opp til det er fikset.
* **Sjekklister:** Strukturerte lister for internkontroll (f.eks. brannslukker, rømningsveier). Brukes til systematisk oppfølging av HMS og vedlikehold.
* **Mine maler:** Opprett egne sjekklistemaler under Sjekklister → Mine maler. Legg til sjekkpunkter, kategori og frekvens – bruk malen til å opprette internkontroll-saker for valgte eiendommer.
* **Opprett fra mal:** På eiendomsdetaljsiden (Styringspanel) kan du velge «Opprett fra mal» for å lage en ny sjekkliste-sak basert på en eksisterende mal (system eller egendefinert).
* **Aktivitetshub:** Tilgjengelige aktivitetsmaler. Legg til for din eiendom fra sjekklister-siden eller eiendomsdetalj.

---

## Avviksanalyse

Avviksanalysen sammenligner **budsjett** med **regnskap** (faktiske utgifter) for en valgt eiendom.

### Slik bruker du den

1. Velg eiendom fra nedtrekksmenyen.
2. Velg år og periode (måned, kvartal, YTD eller år).
3. Se oppsummering: Budsjett, Regnskap, Total avvik og prosent.
4. Graf og tabell viser avvik per kostnadskategori.

---

## Data Governance Dashboard

For å sikre full åpenhet og kontroll over hvordan vi håndterer sensitive data, har BEFS et eget **Data Governance Dashboard**. Dette er verktøyet for deg som trenger oversikt over informasjonssikkerhet og personvern (GDPR).

### Hva finner du her?

* **Dataklassifisering:** Oversikt over alle tabeller i databasen og deres risikonivå (Nivå 1: Public, Nivå 2: Internal, Nivå 3: Restricted).
* **Domene-oversikt:** Data er delt inn i logiske kilder som *Identitet*, *Økonomi*, *Eiendom*, *IoT*, *AI* og *Compliance*.
* **Topologi-graf:** En visuell fremstilling av hvordan datamodellen henger sammen og hvilke områder som er mest sensitive.
* **DPIA (Personvernkonsekvensutredning):** En digital og oppdatert utredning som dokumenterer risiko og tiltak for personvernet i løsningen.

### Hvordan bruke det?

* **Grid-visning:** Bla gjennom alle datatabeller. Klikk på en tabell for å se hvilke kolonner som er klassifisert som sensitive og hvorfor.
* **Graph-visning:** Se det store bildet. Jo rødere punkter, jo mer sensitiv er informasjonen i det området.
* **DPIA-modus:** Les den formelle vurderingen av personvern og sikkerhetstiltak i systemet.

Dashbordet hjelper oss å etterleve lovkrav og sikrer at alle brukere vet at dataene deres blir behandlet på en trygg måte.

---

### Hva vises i analysen

* **Budsjett:** Planlagte beløp for perioden (fra budsjett-tabellen).
* **Regnskap:** Faktisk bokførte utgifter (fra gl_transactions eller manual_expenses).
* **Avvik:** Forskjell (positiv = under budsjett, negativ = over budsjett).
* **Status:** "Akseptabelt" ved avvik under 5 %, ellers "Krever Tiltak".

### Budsjett 2026 og Prediksjon 2027

**Budsjett 2026** ble beregnet fra faktisk GL-regnskap 2025 med kategori-baserte vekstrater:

* **Husleie:** +4,7 % | **Drift:** +10,0 % | **Total: 605 MNOK** (74 eiendommer)

**Prediksjon 2027** er en avansert prediksjon basert på Holt-Winters-algoritmen med historikk tilbake til 2021:

* **Eiendomsdrift: 614,8 MNOK** | **190 eiendommer** | +15,9 % vs 2025 GL
* **Lønnskostnader: 645,3 MNOK** | +30,5 % vs 2025 (Holt-Winters på lønnsserie)
* Se **Prediksjon 2027** i menyen for fullstendig oversikt og interaktiv budsjettjustering.

Predikterte budsjettlinjer lagres med `is_synthetic = true` og er tilgjengelige i avviksanalysen.

### Mangler budsjett eller kostnader?

Avviksanalysen krever **budsjettdata** og **utgiftsdata**. Hvis du får feilmelding:

1. **Budsjett 2026:** Kjør fra backend:
   `python3 scripts/budget_2026_kategori.py`
2. **Eldre budsjett:** Generer fra forbruk:
   `python3 scripts/fill_budget_from_consumption.py`
3. **Utgifter:** Sjekk at eiendommen har løpende utgifter i `gl_transactions` (fra regnskapsimport) eller `manual_expenses`.

---

## Rullerende Prognoser

Rullerende prognoser prosjektear **fremtidige kostnader** basert på historisk regnskap.

### Prognose: Slik bruker du den

1. Velg eiendom fra nedtrekksmenyen.
2. Justér **inflasjonsjustering** (årlig KPI-simulering) med skyveknappen.
3. Velg **prognosehorisont** (12, 24, 36 eller 60 måneder).
4. Grafen viser historiske transaksjoner og fremtidig prognose.

### Parametere

* **Inflasjonsjustering:** Simulerer kostnadsøkning over tid (standard 3,5 %).
* **Prognosehorisont:** Hvor mange måneder frem i tid prognosen strekker seg.
* **Historisk snitt:** Gjennomsnittlig månedlig utgift basert på siste 12 måneder.

### Mangler historiske data?

Prognosen bruker først **gl_transactions** når tilgjengelig. Ellers brukes **manual_expenses** eller **financial_history** for å estimere månedlig forbruk. Sørg for at eiendommen har utgifter registrert (f.eks. fra regnskapsimport).

---

## Prediksjon 2027

**Prediksjon 2027** beregner forventede eiendomskostnader for 2027 for hele porteføljen, basert på historisk GL-regnskap 2021–2025. Siden finnes under **Økonomi**-menyen.

### Algoritme

Systemet bruker **Holt-Winters dobbel eksponensiell utjevning** med dempet trend:

* **α = 0,70** – vekting av nyere år (høy verdi gir stor vekt på siste observasjon)
* **β = 0,30** – trendglattning
* **φ = 0,85** – demping (hindrer ukontrollert vekst)
* **Inflasjonsfallback = 3,5 %** – brukes ved begrenset historikk (< 2 år)

Prediksjon kjøres uavhengig per kostnadskategori (Drift, Investering, Gjennomstrømning) for å fange ulike kostnadsmønstre.

### Nøkkeltall (siste kjøring)

* **Total prediksjon 2027:** 621,6 MNOK
* **Faktisk GL 2025:** 525,9 MNOK
* **Endring:** +18,2 %
* **Antall eiendommer:** 190

### KPI-kort

| Kort | Forklaring |
|------|-----------|
| Total 2027 | Sum prediktert budsjett alle eiendommer |
| 2025 faktisk (GL) | Sum faktiske kostnader fra GL-regnskap 2025 |
| Endring % | Prosentvis endring 2025 → 2027 |
| Eiendommer med pred. | Antall eiendommer det ble generert prediksjon for |

### Fordeling

Tabellen **Fordeling per SRS-kategori** viser Drift, Investering og Gjennomstrømning separat. **Per region** viser tallene for Nord, Midt-Norge, Vest, Sør, Øst og Bufdir.

### Topp 20 eiendommer

Rangering etter størst 2027-budsjett, med kolonnene: Region, GL 2025, Pred. 2027, Endring %.

### Metodebeskrivelse

Klikk på **«Metodebeskrivelse»** nederst på siden for en teknisk forklaring beregnet på revisorer og regnskapsavdelingen. Den beskriver datakilde (GL-transaksjoner, `belop > 0`), algoritme-parametere og at predikterte budsjettlinjer lagres med `is_synthetic = true` i budget-tabellen.

### Generer prediksjoner

Klikk **«Generer prediksjoner»** for å kjøre algoritmen på nytt mot oppdatert GL-data.

---

## SRS-rapport

**SRS-samsvarrapporten** dokumenterer hvordan data i BEFS støtter **Statlig Regnskapsstandard (SRS)**. Siden er særlig laget for **regnskapsavdeling og revisjon**, men gir også regionledere oversikt over kategorisering og koststeddekning.

**Hvor finner du den:** **Økonomi** → **SRS-rapport** (sti i nettleseren: `/financials/srs`).

**Datagrunnlag:** Tallene bygger på **GL-transaksjoner** importert fra Agresso (kategorisering `srs_kategori`), **koststed_mapping** (Dim1 → eiendom), **leie** på kontiene 6300/6310, og **anleggsregisteret** der dette er tatt i bruk.

### År, utskrift og tilgang

1. Velg **år** (2021–2025) i nedtrekkslisten øverst til høyre – alle hovedtall (unntatt flerårstabellen) følger valgt år.
2. Klikk **«Skriv ut / PDF»** for å åpne utskriftsdialogen; bruk «Lagre som PDF» i nettleseren for arkivering eller vedlegg til revisjon.
3. Siden krever rolle **Administrator** eller **Regional leder** (API sperrer andre roller).

### SRS-samsvarsstatus

Øverst på siden vises en **sjekkliste** med fem krav. Hvert punkt har en **statusmerke** og en **kort forklaring** (detaljlinje under).

| Status i listen | Betydning |
|-----------------|-----------|
| OK | Kravet anses oppfylt ut fra tilgjengelige data |
| Delvis | Delvis oppfylt (typisk når terskel for koststedkobling ikke er nådd) |
| Planlagt | Funksjonalitet er beskrevet i veikart, men ikke ferdig i systemet |
| Mangler | Nødvendige data eller mapping finnes ikke |
| Ikke startet | Register eller motor er ikke befolket |

**De fem punktene:**

1. **SRS-kategorisering** – At GL-poster er fordelt på **Drift**, **Investering** og **Gjennomstrømning** (evt. **Ukjent** der konto/BA ikke gir kategori). Detaljen viser antall transaksjoner for valgt år.
2. **Koststed-kobling** – At Agresso **Dim1 (koststed)** er knyttet til en eiendom i BEFS via koststedtabellen. Detaljen viser f.eks. «X av Y koststed koblet (Z %)». Systemet markerer **OK** når minst halvparten av koststedene er koblet; ellers **Delvis**.
3. **SRS 13 – Leie** – At leiekostnader vises på konto **6300** (privat utleier) og **6310** (Statsbygg). Tabellen under vises bare det er poster for året.
4. **SRS 17 – Anleggsmidler** – At **anleggsregisteret** inneholder aktive anleggsmidler med avskrivningsgrunnlag. Er registeret tomt, står punktet som **Planlagt** inntil data er importert/populert.
5. **SRS 10 – Nøytralisering** – Motposter mot statlig finansiering i tråd med avskrivninger. I dag er dette **Planlagt** og knyttet til **fase 3** (avskrivningsmotor og nøytralisering); detaljteksten viser dette eksplisitt.

### SRS-kategorisering (KPI-kort og historikk)

Seksjonen **SRS-kategorisering** viser for valgt år:

* **Sammendrag** – antall transaksjoner og **sum beløp** for alle kategorier til sammen.
* **Tre KPI-kort** (fire hvis **Ukjent** finnes):
  * **Drift** – løpende driftskostnader.
  * **Investering** – investeringer (typisk anleggsrelaterte konti iht. importregler).
  * **Gjennomstrømning** – viderefakturering / gjennomstrømningsposter (f.eks. bestemte bilagsarter).
  * **Ukjent** – poster som ikke fikk kategori ved import.

På hvert kort ser du **beløp**, **antall transaksjoner** og **andel i prosent** av årets total.

**Historikk-tabellen** (vises når det finnes data for flere år) lister **år**, **kategori**, **antall** og **beløp** – slik at du kan sammenligne utvikling over tid. Radene for **valgt år** er visuelt uthevet.

### Koststed-dekning (Dim1 → eiendom)

Her vises **ikke** enkelttransaksjoner, men **registeret** av koststedkoder:

* **Totalt koststed** – antall Dim1-rader i koststed_mapping.
* **Koblet til eiendom** – hvor mange som har `property_id` satt.
* **Ikke koblet** – resten.
* **Dekningsgrad** – prosent koblet; **progressbar** illustrerer andelen.

**Tolkning:** Høy dekning gir bedre **sporbarhet** fra kontering på koststed til konkret eiendom i BEFS. Ukoblede koststed kan være fellesfunksjoner, nye koder eller koder som mangler i vedlikeholdt mapping.

### SRS 13 – Leieavtaler

Tabellen **SRS 13 – Leieavtaler** viser, for valgt år, aggregerte beløp per konto:

| Konto | Typisk innhold |
|-------|----------------|
| 6300 | Leie fra private utleiere |
| 6310 | Leie fra Statsbygg |

Kolonner: **Konto**, **Beskrivelse** (kontonavn fra GL), **Type** (Privat / Statsbygg), **Antall bilag**, **Total beløp**. Finnes ingen poster for året, vises en tydelig tom tilstand.

### SRS 17 – Anleggsmidler (oppsummering)

Kortene viser **totalt antall** linjer i anleggsregisteret, hvor mange som er **aktive**, og **sum bokført verdi** for aktive anlegg. Er registeret ikke tatt i bruk, vises et **informasjonsfelt** om at fase 3 vil populere fra GL (kontoer som 1268/4960, terskel 50 000 kr) og koble til avskrivning.

For **detaljert liste, avskrivningsplan og import**, bruk siden **Anleggsregister** under Økonomi (egen seksjon i denne hjelpen).

### SRS 10 – Nøytralisering (planlagt)

Nøytralisering (motbilag mot finansiering) er **ikke** produksjonssatt ennå; status i sjekklisten er **Planlagt** til avskrivningsmotor og tilhørende logikk er levert.

### Relaterte sider

* **Anleggsregister** – detaljer om anleggsmidler, avskrivning og import.
* **Prediksjon** og **Eiendomskostnader** – bruker samme SRS-kategorier der det er relevant for budsjett og analyse.

---

## Anleggsregister – SRS 17

**Anleggsregisteret** holder oversikt over balanseførte anleggsmidler (investeringer ≥ 50 000 NOK) og beregner lineær avskrivning over gjenværende leieperiode, i henhold til SRS 17. Siden finnes under **Økonomi**-menyen.

### KPI-kort

| Kort | Forklaring |
|------|-----------|
| Anleggsmidler | Antall aktive poster |
| Bokført verdi | Samlet bokført verdi per 01.01.2025 |
| Årlig avskrivning | Sum avskrivning konto 6010 (SRS 17) |
| Avskr. 2025 | Årets avskrivning |

### Avskrivningsplan

Tabellen **Avskrivningsplan 2025–2033** viser per år: restverdi inngående, årets avskrivning og restverdi utgående.

### Anleggsliste

Søkbar liste over alle anleggsmidler:

| Kolonne | Forklaring |
|---------|-----------|
| Navn | Beskrivelse av anleggsmidlet |
| Koststed | GL Dim1-kode |
| Konto | GL-konto (f.eks. 1268, 4960) |
| Anskaffelse | Anskaffelseskost |
| Bokført | Nåværende bokført verdi |
| Mnd. avskr. | Månedlig avskrivningsbeløp |
| Leieslutt | Dato avskrivning avsluttes |
| Status | Aktiv / Avsluttet |

### Terskel og import

Kun poster med anskaffelseskost **≥ 50 000 NOK** aktiveres. Klikk **«Importer anleggsmidler fra GL»** for å populere registeret fra GL-transaksjoner (kjøres av administrator).

---

## Sjekklister og internkontroll

Siden **Sjekklister** viser dine planlagte internkontroll-oppgaver og lar deg fullføre sjekkrunder.

### Sjekklister: Slik bruker du den

* **Mine sjekklister:** Se åpne saker med sjekkpunkter. Klikk «Start Sjekk» for å gå gjennom punktene og fullføre.
* **Fullfør sjekkliste:** Kryss av for hvert punkt og klikk «Fullfør Sjekkliste» – saken lukkes og lagres.
* **Mine maler:** Opprett egne sjekklistemaler (tittel, beskrivelse, kategori, frekvens, sjekkpunkter). Rediger eller slett maler du eier.
* **Opprett sak fra mal:** På hver mal kan du velge eiendom og opprette en ny internkontroll-sak. På eiendomsdetaljsiden bruk «Opprett fra mal» i Styringspanel.
* **Opprett internkontroll-saker:** For en eiendom kan du klikke «Opprett internkontroll-saker» for å generere standard saker (RKL6, brannvern m.m.).
* **Aktivitetshub:** Lenke til tilgjengelige aktivitetsmaler.

### Hva er avvik?

Avvik er avvikelser fra krav eller plan: manglende dokumentasjon, forfalt inspeksjon, HMS-brudd, vedlikeholdsbehov m.m. Systemet kobler avvik til sjekklister og internkontroll.

---

## Avvik & Risiko

Siden **Avvik & Risiko** gir oversikt over registrerte avvik og risikofaktorer som krever oppfølging.

### Avvik: Slik bruker du den

* **Se avvik:** Listen viser alle avvik med filtrering (f.eks. etter prioritet).
* **Meld avvik:** Klikk "Meld Avvik" for å registrere nytt avvik (eiendom, type, alvorlighetsgrad, beskrivelse).
* **Risikostats:** Oversikt over antall avvik og risikonivå.
* **Åpne detaljer:** Klikk på et avvik for å se mer og følge opp.

---

## Risikobildet

**Risikobildet** viser eiendommer sortert etter **prioriteringsindeks** – brukes til å styre hvor midler bør prioriteres. Basert på drift (avvik), bygningsmasse og eksterne faktorer (NVE).

### Risikobildet: Slik bruker du den

* **Prioritert watchlist:** Eiendommer sortert etter prioriteringsindeks (risikoscore × årskostnad).
* **Kolonner:** Eiendom, Score, Kategori, Årskostnad, Budsjett, Prioritet, Reservefaktor, Åpne avvik.
* **Kritisk/Høy risiko:** Antall eiendommer med høy score.
* **Detaljer:** Klikk «Se detaljer» for å åpne eiendomsdetalj med NVE-notater og risikofaktorer.

### Prioriteringsindeks

**Prioritet = risikoscore × årskostnad.** Brukes til beslutningsstøtte – «dette er hvor midler bør prioriteres først», ikke forventet tap. Årskostnad = husleie + utgifter. Reservefaktor (1,5 / 1,0 / 0,5) brukes til dimensjonering av buffer.

### Risikoscore

Scoren kombinerer flere faktorer (avvik, tiltak, ekstern risiko). Høyere score = større oppfølgingsbehov. NVE-notater beskriver flom- og skredfare.

---

## BUP Lokasjoner

Oversikt over **Barne- og ungdomspsykiatriske poliklinikker** (BUP) i Norge.

### BUP: Slik bruker du den

* **Søk:** Skriv adresse eller region i søkefeltet for å filtrere listen.
* **Liste:** Tabellen viser adresse, region, telefon og koordinater for hver lokasjon.
* **Bruk:** Nyttig når du vurderer tilgjengelighet til BUP-tjenester for eiendommer (f.eks. barnevernsinstitusjoner).

---

## SSB Statistikk

**SSB Statistikk**-siden gir tilgang til offisiell norsk statistikk fra Statistisk sentralbyrå direkte i BEFS. Ingen innlogging eller API-nøkkel kreves.

Finn siden under **DATA & STATISTIKK** i sidebaren, eller gå til `/ssb`.

### Faner

* **Søk tabeller:** Søk i SSB Statbank på norsk eller engelsk (f.eks. «KPI», «byggekostnad»). Velg en tabell for å gå videre til datahenting.
* **Hent data:** Hent tall for valgt tabell; du kan begrense tidsomfang (f.eks. siste perioder) der tabellen støtter det.
* **Kombiner med BEFS:** Samstill SSB-serier med BEFS-regnskapsdata.
* **Analyser og rapporter:** KI-støttede analyser og rapporter på tvers av SSB- og porteføljedata.

### Nyttige SSB-tabeller for eiendomsforvaltning

| Tabell | Innhold | Bruksområde |
|--------|---------|-------------|
| KPI | Konsumprisindeks, alle grupper | Kontraktsregulering, budsjettanslag |
| Byggekostnadsindeks | Kostnadsvekst for bygg | Vurdere vedlikeholdsbudsjett |
| Leieprisindeks næringslokaler | Markedsleie per kvm | Sammenligne mot egne kontrakter |
| Folkemengde | Befolkningsutvikling per kommune | Behovsanalyse for BUP/barnevern |

### KI-Kollega og SSB

KI-Kollega kan hente og analysere SSB-data direkte i chatten:

* **Spør om statistikk:** «Hva er KPI nå?» → KI-Kollega henter siste verdi fra SSB og viser tabellen.
* **Sammenlign med BEFS:** «Sammenlign våre husleiekostnader med KPI de siste 5 årene» → KI-Kollega henter SSB-data og samstiller med GL-regnskap.
* **Markedsleie:** «Hva er markedsleie for næringslokaler i Oslo?» → KI-Kollega slår opp SSB-leieprisindeksen.

---

## Lovdata Søk

Søk i **lover, forskrifter og rettsinformasjon** direkte fra BEFS via Lovdata.

### Lovdata: Slik bruker du den

1. Skriv søkeord (f.eks. "plan- og bygningsloven" eller "leieavtale").
2. Klikk Søk.
3. Resultatene vises med lenker til Lovdata.no for full tekst.

### Lovdata Tips

Ved feilmelding om integrasjon: Sjekk at Lovdata API er konfigurert. Resultatene åpnes på lovdata.no.

---

## AI Research Lab

**AI Research Lab** er et verktøy for å eksperimentere med KI og finansiell analyse.

### AI Research Lab: Slik bruker du den

* **Chat:** Still spørsmål og få svar med støtte fra KI.
* **Verktøybibliotek:** Se og administrer tilgjengelige KI-verktøy (søk, pin, publiser).
* **Finansiell panel:** Spesialiserte spørringer om økonomi og kostnader.

### Bruk

Labben er ment for avanserte brukere og utvikling/testing av nye KI-funksjoner.

---

## Barnevern – Kostnadssimulering

**Barnevern**-siden kombinerer BEFS institusjonsdata med statlig egenandel per plass for å simulere kostnader ved ulike bruksgrader. Siden finnes under **DATA & STATISTIKK** i sidebaren.

### Plasser og institusjoner

Oversiktstabellen viser per region: antall godkjente plasser og totale kostnader 2025. Klikk på en region for å gå til institusjonslisten for den regionen.

### Slik bruker du simuleringen

1. Velg **år** (2024–2030) for å bruke riktig egenandelsats.
2. Juster **bruksgrad** (0–100 %) med skyveknappen – hvor stor andel av plassene som er i bruk.
3. Les av resultatene i KPI-kortene.

### KPI-kort

| Kort | Forklaring |
|------|-----------|
| Brukte plasser | Antall plasser i bruk (godkjente × bruksgrad) |
| Ubrukte plasser | Ledige plasser (kostnadsbyrde) |
| Kostnad brukte | Statlig egenandel × brukte plasser (inntektspotensial) |
| Kostnad ubrukte | Kostnad for tomme plasser (rødt) |
| Total kostnad | Sum alle plasser |

### Egenandel

Statlig egenandel per plass per måned (ordinær institusjon):

| År | Egenandel |
|----|----------|
| 2024 | 182 700 kr |
| 2025 | 190 190 kr |
| 2026 | 197 225 kr |
| 2027 | 204 650 kr |

### SSB KOSTRA

Nasjonal sammenligningsverdi hentes fra SSB tabell 12279 (KOSTRA barnevern) for «Landet». Brukes til å sette Bufetats tall i nasjonal kontekst.

---

## Media Overvåkning

**Media Overvåkning** kjører automatisk sentimentanalyse av leietakerne (parter) i systemet. Analysen oppdateres nattlig kl. 02:30. Siden er begrenset til administratorer.

### Oversikt

Fire KPI-kort øverst:

| Kort | Forklaring |
|------|-----------|
| Analyserte leietakere | Totalt antall parter som er analysert |
| Negative | Score ≤ 4 (rødt) |
| Nøytrale | Score 5–6 (gult) |
| Positive | Score ≥ 7 (grønt) |

### Rangeringsliste

Alle leietakere vises i en rangert liste med:
* **Sentimentscore 1–10** med visuell indikator
* **Rød pil ↓** = negativ trend, **grønn pil ↑** = positiv trend
* Antall aktive kontrakter

Klikk på en rad for å utvide og se:
* 🚩 **Røde flagg** – negative funn (konkursfare, inkasso, negativ omtale)
* ✅ **Positivt** – positive funn
* Tidsstempel for siste oppdatering og antall sjektede kilder
* Lenke til leietakerprofilen i BEFS

### Filtrering

* Tekstsøk på leietakernavn eller org.nr.
* Filterknapper: **Alle** / **🔴 Negative** / **🟢 Positive**

### Scorer

| Score | Farge | Tolkning |
|-------|-------|---------|
| 1–3 | Rød | Svært negativ |
| 4–5 | Oransje | Negativ / blandet |
| 6–7 | Gul | Nøytral |
| 8–10 | Grønn | Positiv |

### Manuell kjøring

Klikk **«Kjør nå»** for å starte analysen umiddelbart (tar noen minutter avhengig av antall leietakere). Et statusbanner vises mens analysen pågår.

---

## Innstillinger

På **Innstillinger**-siden kan du justere brukerpreferanser og systemvalg.

### Min Profil

* **Navn** og **e-post:** Viser innlogget bruker.
* **Rolle:** Din tilordnede rolle (f.eks. Eiendomsforvalter).

### Systeminnstillinger

* **Mørk modus:** Slå av/på mørkt tema via lyspære-ikonet i headeren (øverst til høyre).
* **E-postvarsling ved avvik:** Varsler når nye avvik registreres.
* **Lyd for varsler:** Lydvarsling for hendelser.

### Systemstatus

Viser tilkoblingsstatus til Backend API og database.

---

## Tilgjengelighet og personvern

Egne informasjonssider (lenket fra brukerhjelpen på `/help`):

* **`/tilgjengelighet`** – tilgjengelighetserklæring (UU) for løsningen.
* **`/personvern`** – hvordan personopplysninger behandles i tråd med personvernreglene.

---

## Admin & Verktøy (for administratorer)

Admin-dashboardet gir tilgang til administrative funksjoner. Krever admin-rolle.

### Tilgjengelige verktøy

* **Ekstern Risiko:** Kjør batch-oppdatering av ekstern risiko (NVE, Kartverket) for hele porteføljen.
* **Risikobildet:** Lenke til risikooversikt.
* **Finansiell Analyse:** Søk, sammenlign og analyser kostnader på tvers av eiendommer.
* **Rollesimulering:** Test systemet med ulike roller (Eiendomsforvalter, Vaktmester, Leietaker) uten å logge ut.
* **HMS Kalender:** Oversikt over planlagte HMS-aktiviteter.
* **Brukeradministrasjon:** Administrer brukerroller og tilganger.
* **Konkursovervåkning:** `/konkurs-monitor` – BRREG-sjekk av alle parter (se egen seksjon).
* **Agresso CSV-lab:** `/agresso-csv` – validering av regnskapsuttrekk før import (se egen seksjon).
* **KI-Lab & Transparens, Data Governance, dokumentimport m.m.:** Tilgjengelig fra Admin-dashboard etter rolle.

### Admin Tips

Batch-oppdatering av ekstern risiko kan ta tid avhengig av antall eiendommer.

### Rollesimulering

Som administrator kan du midlertidig bytte rolle for å se hvordan systemet ser ut for andre brukere.

1. Klikk på **"Bytt rolle"** i headeren (øverst til høyre).
2. Velg ønsket rolle (f.eks. Eiendomsforvalter).
3. Systemet lastes på nytt med begrensede rettigheter.
4. For å avslutte, klikk på **"Simulering"** og velg **"Ingen (Admin)"**.

Dette er nyttig for brukerstøtte og feilsøking. Merk at admin-menyen i sidebaren skjules under simulering.

---

## Finansiell Innsikt (Admin)

Avansert **finansiell analyse** for administratorer. Søk og sammenlign kostnader på tvers av eiendommer.

### Finansiell Innsikt: Slik bruker du den

1. Søk på eiendomsnavn, adresse eller region (minst 2 tegn).
2. Klikk på et treff for å se detaljert analyse.
3. Se kostnader per kategori, per leverandør, kontrakter og status.

### Hva vises

* **Status:** Complete, missing_costs, missing_rent eller missing_all.
* **Kostnader per kategori:** Fordeling av utgifter.
* **Kostnader per leverandør:** Hvem pengene går til.
* **Kontrakter:** Leie og datoer.

---

## Leverandørkontroll og Risikostyring (v2.0)

For å sikre at vi kun handler med seriøse leverandører og oppfyller kravene i Hvitvaskingsloven, har systemet nå en aktiv **Risikomotor**.

### Slik fungerer det for deg

Når du går inn på en leverandør (under **Parter**), vil du se en risikoindikator øverst:

*   🟢 **GRØNN (Lav):** Trygt. Ingen anmerkninger.
*   🟡 **GUL (Moderat):** Vær årvåken (f.eks. nytt selskap). Sjekk leveranse.
*   🔴 **RØD (Høy):** **STOPP!** Kontakt økonomisjef. (Eks: Skattegjeld, inkasso).
*   ⚫ **SVART (Kritisk):** **BLOKKERT.** Leverandøren er sperret for betaling. (Eks: Konkurs, sanksjoner).

### Hva sjekkes?
Systemet sjekker automatisk:
1.  **BRREG:** Konkursstatus og roller.
2.  **Økonomi:** Regnskapstall og insolvensfare.
3.  **Heftelser:** Pant i driftstilbehør (Løsøreregisteret via Maskinporten).
4.  **Compliance:** Sanksjonslister (EU/FN) og skatt (eBevis*).
5.  **Intern adferd:** Endring av bankkonto og uvanlige fakturaer (Unit4).

### Fullstendig instruks
For detaljerte rutiner og handlingsplikt, se den egne instruksen:
👉 **[Instruks for Leverandørkontroll](LEVERANDOR_RISIKO.md)**

---

## Styringspanel (eiendomsdetalj)

På eiendomsdetaljsiden vises et **Styringspanel** i høyre kolonne med nøkkeltall for prioritering:

* **Risikoscore:** 0–100, brukes som prioriteringsparameter.
* **Årlig kostnad:** Husleie + utgifter (OPEX + CAPEX).
* **OPEX / CAPEX:** Driftskostnader vs. investeringer.
* **Budsjettdekning:** Budsjett som andel av årlig kostnad.
* **Åpne avvik:** Antall avvik i internkontroll som venter på oppfølging.

---

## BEFS Analytics Dashboard

Dashboardet viser sanntidsanalyse av eiendomsporteføljen med nøkkeltall og diagrammer. Hold musepekeren over titler for forklaring.

### Nøkkeltall (KPI-er)

* **Netto Yield:** (Årlig leie − Vedlikehold) ÷ Årlig leie. Avkastning på porteføljen.
* **Aktive Kontrakter:** Antall leie- og serviceavtaler med status «aktiv».
* **Ledighet:** Andel enheter uten aktiv kontrakt.
* **Total Årlig Leie:** Sum leie fra alle aktive kontrakter.
* **Total Vedlikehold:** Sum bokførte vedlikeholds- og driftsutgifter.

### Diagrammer

* **Regional Finansiell Oversikt:** Leie og vedlikehold per region (Nord, Midt-Norge, Vest, Sør, Bufdir).
* **Regional Sammenligning:** Søylediagram med leie (blå) og vedlikehold (oransje) per region. Lav eller null leie for en region betyr at regionen har få eller ingen aktive kontrakter – sjekk at kontrakter er registrert.
* **Vanligste Kostnadskategorier:** Fordeling av utgiftstyper på tvers av eiendommer.

---

## Økonomi og Finans – Regional oversikt

Siden **Økonomi og Finans** (`/financials`, Økonomi-menyen) samler økonomiske analyser for hele porteføljen. Velg **år** der det er relevant.

### Faner og visninger

* **Regional oversikt:** Nøkkeltall og fordeling per region (leie, vedlikehold, budsjett, antall eiendommer).
* **Leverandører:** Utgifter gruppert på leverandør.
* **Katalog:** Kontokatalog / kostnadsstruktur (oversikt over konti og klassifisering).
* **Fakturaer:** Bilags-/fakturalinjer fra GL der dette er tilgjengelig.
* **Mønstre:** Kostnadsmønstre og trender på tvers av eiendommer.
* **Transaksjoner:** Detaljert transaksjonsutforsker for dypdykk i regnskapsposter.
* **Mangler kostnader:** Eiendommer eller koststed som mangler kostnadsdata for valgt år.
* **Avviklet eiendom:** Eiendommer som ikke finnes i budsjettgrunnlaget for valgt år og samtidig ikke har GL-kostnader i året (uten aktivitet).
* **Kostnader uten eiendom:** Poster som ikke er koblet til eiendom (inkl. pivot-visning for å fordele eller analysere).
* **Kontraktsoversikt (pivot):** Pivot-tabell over kontrakter og tilhørende økonomi.

### Forbruk siste 3 år

**Forbruk** betyr her **totale utgifter** – ikke bare strøm, men alle kostnader for eiendommen/regionen i det aktuelle året (vedlikehold, strøm, fellesutgifter, renhold m.m.). Tallene vises per år (f.eks. 2023, 2024, 2025) og kommer fra historisk finansdata (`financial_history`). Data kan være importert eller syntetisk generert fra dagens utgifter. Hold musepekeren over «Forbruk siste 3 år» for tooltip-forklaring.

### Avviklet eiendom (datakvalitet)

Fanen **Avviklet eiendom** er laget for å finne eiendommer som i praksis er ute av aktiv bruk i valgt år.

En eiendom havner i listen når begge vilkår er oppfylt:

* Eiendommen har **ikke** budsjettposter i valgt budsjettår.
* Eiendommen har **ingen** GL-kostnader i valgt kostnadsår.

Dette er strengere enn «ikke i budsjett»: eiendommer med faktiske kostnader blir ikke vist som avviklet.

---

## Finansiell oversikt og Kostnadsanalyse

På eiendomsdetaljsiden finner du **Finansiell oversikt** og **Kostnadsanalyse**.

### Husleie (YTD)

* **Med kontrakter:** Sum av årlig leie fra alle aktive kontrakter.
* **Uten kontrakter:** Systemet viser et **syntetisk estimat** basert på areal og vedlikeholdskostnader fra masterdata. Dette er merket med "(estimat)".

### Mangler enheter

Hvis du ser **"Mangler enheter"**, betyr det at eiendommen ikke har registrerte **enheter** (leiligheter/lokaler). Uten enheter kan det ikke opprettes kontrakter. Leie-estimatet er da basert på areal og vedlikehold og kan være unøyaktig. **Løsning:** Legg til enheter for bedre tall.

### Bokførte kostnader

Sum av alle utgifter fra regnskap (CSV-import) og manuelle poster. Kilde: Masterdata + Regnskap.

### Kostnadsanalyse – hvordan beregnes den?

Kostnadsanalysen sammenligner bokførte kostnader med husleie og kategoriserer utgiftene. Når det finnes syntetisk husleie-estimat (ingen aktive kontrakter), brukes dette i beregningen – du får da "Forhold til husleie" og "vs husleie X kr (estimat)" i stedet for "Mangler husleiedata".

#### Beregningsformel

**Forhold til husleie** = (Bokførte kostnader ÷ Husleie) × 100 %.  
Eksempel: 21 911 kr ÷ 2 317 060 kr ≈ 1 %.

#### De fire kostnadskategoriene

Systemet fordeler utgiftene i fire kategorier:

| Kategori | Eksempler på utgiftstyper |
| :--- | :--- |
| **Eiendomskostnader** | Leie lokaler, fellesutgifter, leie parkeringsplass |
| **Driftskostnader** | Strøm/oppvarming, renhold, vakthold, renovasjon, annen kostnad lokaler, reparasjon/vedlikehold |
| **Investeringer** | Fast inventar over 50 000 kr, oppgradering, ombygging, risikoavsetning |
| **Andre kostnader** | Utgifter som ikke passer i de andre kategoriene |

#### Statusvurdering

Basert på forholdet mellom totale kostnader og husleie vises en av disse statusene:

| Status | Betydning |
| :--- | :--- |
| **NORMAL** | Kostnader er innenfor forventet nivå |
| **MODERAT** | Totale kostnader er over 1,5× husleie |
| **HØY** | Totale kostnader er over 2× husleie |
| **KRITISK** | Totale kostnader er over 3× husleie |

#### Anomalier og duplikater

* **Anomalier:** Enkeltposter over 500 000 kr markeres som uvanlig høye.
* **Potensielle duplikater:** Systemet varsler hvis flere poster har samme leverandør og beløp (mer enn 2 like poster).

---

## Dokumenthåndtering og PDF-analyse

BEFS har avansert støtte for **PDF-dokumenter** med automatisk tekstekstraksjon, tabell-gjenkjenning og intelligent søk.

### Last opp PDF-dokumenter

Du kan laste opp PDF-filer til kontrakter og eiendommer:

1. Gå til kontraktsiden eller eiendomsdetaljsiden.
2. Klikk på **«Last opp dokument»** eller dra-og-slipp PDF-filen.
3. Systemet analyserer automatisk dokumentet og ekstraherer:
   * **Tekst:** All lesbar tekst fra PDF-en.
   * **Tabeller:** Prislister, kostnadsoppstillinger og andre tabelldata.
   * **Metadata:** Dokumenttittel, forfatter, antall sider og opprettelsesdato.

### Søk i PDF-dokumenter

KI-Kollega kan søke i opplastede PDF-er:

* **Eksempel:** "Hva står det om oppsigelsestid i kontrakten for Storgata 12?"
* **Resultat:** KI-Kollega finner relevant tekst fra PDF-en og viser kildelenke til dokumentet.

### Tabellekstraksjon

Systemet gjenkjenner automatisk tabeller i PDF-dokumenter:

* **Prislister:** Leiepriser, serviceavgifter per enhet.
* **Kostnadsoppstillinger:** Vedlikeholdskostnader, budsjettdetaljer.
* **Kontraktsvilkår:** Tabellariske oversikter over avtaleforhold.

Tabeller lagres som strukturerte data og kan brukes i analyser og rapporter.

### Skannede dokumenter (OCR)

For eldre, skannede PDF-er uten tekstlag bruker systemet **OCR (Optical Character Recognition)**:

* Automatisk tekstgjenkjenning fra bilder.
* Støtte for norsk og engelsk.
* Samme søkefunksjonalitet som for vanlige PDF-er.

### Tips for beste resultat

* **Kvalitet:** Bruk PDF-er med god oppløsning for best OCR-resultat.
* **Filnavn:** Gi dokumentene beskrivende navn (f.eks. "Leiekontrakt_Storgata12_2024.pdf").
* **Tagging:** Legg til tags på dokumenter for enklere filtrering og søk.

---

## Innboks

**Sti:** `/innboks` (HOVEDMENY → Innboks).

Innboksen viser **systemvarsler** knyttet til internkontroll og analyse, for eksempel når en eiendom flagges for uvanlig mønster (ML-anomalier) eller når det finnes relaterte **saker**. Når du åpner et varsel, markeres det gjerne som lest, og du sendes til riktig eiendom eller sak.

---

## Jira-integrasjon

**Sti:** `/jira` (INTEGRASJONER → Jira).

Her kan du **opprette Jira-oppgaver** direkte fra BEFS uten å gå via KI-Kollega. Saker opprettes i det konfigurerte Jira-prosjektet (standard oppsett refererer til prosjektet **KAN (BEFS)** – avhengig av miljøkonfigurasjon). Vanlige issuetyper inkluderer **Epic** og **Oppgave**. Du kan legge til **etiketter** for bedre sporbarhet. Etter opprettelse åpnes saken ofte i ny fane.

Dette er et supplement til **KI-Kollega**, som også kan foreslå og opprette saker etter godkjenning i chatten.

---

## Institusjoner

**Sti:** `/institusjoner` (DATA & STATISTIKK).

Siden gir **kapasitetsoversikt** for barnevernsinstitusjoner knyttet til eiendommer i porteføljen: godkjente og budsjetterte plasser, kostnader, regionfilter og søk. Du kan sortere tabellen (f.eks. på navn, region, kost per plass) og velge om **lukkede** institusjoner skal vises. Bruk dette sammen med **Barnevern**-siden for simulering og **BUP-lokasjoner** for geografisk kontekst.

---

## Analyse og innhold

**Sti:** `/analysis` (Analyse & Innsikt i menyen).

Siden samler **analysemoduler** i kategorier (geografi, kontrakter, avvik, risiko, vedlikehold, PDF, dashboarder). Når du velger en modul, sendes en forespørsel til **KI-agenten** (backend) som genererer et tekstsvar (og kan foreslå visualiseringer) basert på modultittel og beskrivelse. Bruk **søkefeltet** øverst for å filtrere moduler.

Nederst til høyre finnes knappen **«Din KI assistent»** for en generell dialog om hvilke analyser som kan kjøres.

> Analyse-siden er ment for **utforskning og beslutningsstøtte**; resultater bør verifiseres mot underliggende data i eiendoms- og økonomivisninger der det er kritisk.

---

## Kontroll 2027

**Sti:** `/kontroll-2027`.

Verktøyet er rettet mot **regnskap, intern kontroll og kontrollører** som skal gjennomgå **GL-data for 2025** og **prognose 2027** før rapportering eller signering.

### Innhold

* **Outlier-analyse:** Transaksjoner, eiendommer og kontoer som skiller seg statistisk ut (f.eks. Z-score, år-over-år), samt **foreldreløse** transaksjoner (uten kobling til eiendom der det er relevant).
* **Prognosegjennomgang:** Eiendommer med **HØY** eller **MIDDELS** risiko i forhold til prediksjon (f.eks. flagg som høy vekst, manglende prediksjon).
* **Samlet vurdering:** Tekstlig konklusjon om materialet er klart for intern kontroll, basert på antall høyrisiko-funn.

Du kan **skrive ut** siden for arkivering. Siden krever at API-endepunktene for finansielle utligere (`/financials/outliers`, `/financials/prognose-review`) returnerer data; ved feil vises melding i grensesnittet.

---

## Konkursovervåkning

**Sti:** `/konkurs-monitor` (kun **Administrator** – egen blokk i sidefeltet).

Siden viser **parter (leietakere)** som BRREG-sjekken har flagget med **konkurs, avvikling eller tilsvarende risiko**. Kjøring skjer **nattlig** (typisk ca. kl. 03:00); administrator kan også starte **«Kjør sjekk nå (alle parter)»** og oppdatere listen. Bruk dette som supplement til **Leverandørkontroll** og **Media Overvåkning** når du vurderer motpart risiko.

---

## Dataordliste og begreper

**Sti:** `/governance/glossary`.

En egen side med **ordliste og begreper** knyttet til data, klassifisering og styring i løsningen. Nyttig når du trenger felles definisjoner på tvers av økonomi, eiendom og compliance. For full **datakatalog og DPIA**-kontekst, se **Data Governance** under Admin (`/admin/governance`).

---

## Ofte stilte spørsmål (FAQ)

**Q: Må jeg skrive helt presist for at KI-Kollega skal forstå?**
A: Nei. KI Kollega forstår forkortelser (fvk, BUP), synonymer (leietakere = parter, billigste per kvm = lavest kostnad per kvm) og vanlige skrivefeil. Skriv som du vil – systemet tolker intensjonen.

**Q: Kan KI-Kollega gjøre feil?**
A: Ja, som alle systemer kan den misforstå. Men i motsetning til "ChatGPT", hallusinerer den ikke tall. Den slår opp i den faktiske databasen vår. Ser du noe rart, dobbeltsjekk kilden – alle svar har en **Kilder**-seksjon med klikkbare lenker til eiendommer, kontrakter, dokumenter, Lovdata eller web.

**Q: Hvor kommer tallene fra?**
A: Vi henter data direkte fra økonomisystemet (Hovedboken) og de digitaliserte kontraktene våre.

**Q: Er dette sikkert?**
A: Ja. Du logger inn med din Google-bruker, og systemet vet nøyaktig hva du har lov til å se og ikke se.

**Q: Hva betyr "syntetisk estimat"?**
A: Når eiendommen ikke har aktive kontrakter, beregner systemet et estimat for husleie basert på areal og vedlikeholdskostnader. Dette brukes i kostnadsanalysen for å gi en indikativ vurdering.

**Q: Hva er risikovurdering (Due Diligence) for parter?**
A: En automatisk sjekk av leietaker/eier (bedrift) mot nettsøk. Systemet leter etter konkursfare, rettssaker, negativ omtale og økonomiske signaler, og gir en risikovurdering (LAV/MIDDELS/HØY) med røde flagg. Nyttig før kontraktsforhandlinger.

**Q: Hvilken KI-Kollega-modus bør jeg velge?**
A: KI-Kollega bruker én samlet modus som automatisk velger riktige verktøy. Du trenger ikke velge – bare still spørsmålet ditt.

**Q: Kan KI-Kollega hente SSB-statistikk?**
A: Ja. KI-Kollega har to SSB-verktøy: ett for å hente tabelldata direkte fra SSB PxWeb, og ett for å samstille SSB-data med BEFS regnskap. Eksempel: «Hva er KPI nå?» eller «Sammenlign husleiekostnadene våre med KPI».

**Q: Hva er budsjett 2026 og Prediksjon 2027 basert på?**
A: Budsjett 2026 er basert på faktisk GL-regnskap 2025 (567 MNOK) med vekstrater: husleie +4,7 %, drift +10,0 % → 605 MNOK for 74 eiendommer. Prediksjon 2027 bruker Holt-Winters-algoritmen (α=0,70, β=0,30, φ=0,85) mot historikk 2021–2025 → 621,6 MNOK for 190 eiendommer. Se seksjonen «Prediksjon 2027» i hjelpen for tekniske detaljer.

**Q: Hvorfor er «Oversikt» i menyen annerledes enn siden /oversikt?**
A: Menypunktet «Oversikt» åpner **dashboard** (`/dashboard`). Siden **`/oversikt`** er en egen **full porteføljeliste** med alle eiendommer, enheter, kontrakter og leietakere (tilgangsfiltrert) og prognoseseksjon – bruk den når du trenger komplett liste, ikke bare KPI-kort.

**Q: Hvor oppretter jeg Jira-saker uten å bruke chat?**
A: Gå til **INTEGRASJONER → Jira** (`/jira`) og fyll ut skjemaet der.

**Q: Hva er forskjellen på «Analyse & Innsikt» og KI-Kollega?**
A: **Analyse & Innsikt** (`/analysis`) starter forhåndsdefinerte analyseforespørsler via **agent-API** (modulknapper). **KI-Kollega** er den generelle chatten nede til høyre. Begge kan overlappe i innhold, men har ulike innganger.

---

## Personvern og Datasikkerhet (GDPR)

BEFS tar ditt personvern på alvor.

### Dine Rettigheter
* **Innsyn:** Du kan be om å få se hvilke data som er lagret om deg.
* **Sletting:** Du kan be om at dine persondata (navn, e-post, telefon) blir slettet eller anonymisert når du slutter i jobben.
* **Sikkerhet:** Tilgang til systemet er strengt kontrollert. Kun autorisert personell har tilgang til finansiell informasjon og personopplysninger.

---

## Historisk dokumentasjon (arkiv) – for administratorer

Utdatert dokumentasjon er flyttet til mappen **`arkiv/`** i prosjektet for å holde root og backend ryddig. Innholdet er beholdt som referanse.

**Kategorier i arkiv:**

| Mappe | Innhold |
| :--- | :--- |
| `arkiv/deploy_og_legacy/` | Deploy, Legacy Infrastructure, secrets, migrering |
| `arkiv/auth_og_login/` | Login-fiks, session, 401, NextAuth |
| `arkiv/rbac_og_roller/` | RBAC-faser, brukerrettigheter |
| `arkiv/google_og_email/` | Google login, e-postverifikasjon, MFA |
| `arkiv/diagnostikk_og_test/` | Diagnostikk- og testdokumenter |
| `arkiv/diverse_historisk/` | Øvrige guider og oppsummeringer |
| `arkiv/backend_deploy_fix/` | Utdaterte deploy/fix-dokumenter |

Se **`arkiv/README.md`** i prosjektet for full oversikt. For oppdatert prosedyre: Brukerhjelp i appen og Admin → Teknisk dokumentasjon.

---

## Oversikt – Prognose 2027 (full porteføljeliste)

Siden **`/oversikt`** (full porteføljeliste – ikke det samme som dashboard `/dashboard`) har en seksjon som viser prognosen for 2027 for hele porteføljen, fordelt på region og eiendom, i tillegg til sammenleggbare lister over eiendommer, enheter, kontrakter og leietakere (tilgangsfiltrert).

### Hva vises

* **Totalt budsjett 2027** – estimert porteføljekostnad basert på Holt-Winters-prediksjon (se *Prediksjon 2027* for metodebeskrivelse)
* **Per region** – søylediagram som sammenligner regionene
* **Drilldown per eiendom** – klikk på en region for å se estimat per eiendom i den regionen
* **Administrative kostnader** – GL-transaksjoner uten tilknyttet eiendom (regionale fellesutgifter) vises separat, estimert med inflasjon fra 2025-aktuals

### Slik bruker du det

1. Gå til **`/oversikt`** (skriv stien i nettleseren eller bruk bokmerke) – menypunktet «Oversikt» peker til dashboard; denne siden er et supplement for komplett porteføljedata.
2. Bla ned til seksjonen **«Prognose 2027»**
3. Klikk på en region i grafen for å se eiendomsnivå
4. Hold musepekeren over en søyle for å se kronebeløp og endring fra 2025

### Datakilde

Prognosen hentes fra `budget`-tabellen (`data_source = holt_winters_2027`). Eiendommer uten prediksjon (utilstrekkelig historikk) vises ikke. Administrative kostnader beregnes fra GL-aktuals 2025 justert med 3,5 % inflasjon.

---

## Agresso CSV-lab

**Agresso CSV-lab** er et verktøy for regnskapsavdelingen og dataansvarlige til å analysere og validere regnskapsuttrekk fra Agresso (Unit4) før de importeres i BEFS.

**Sti i appen:** **`/agresso-csv`** (egen side; ikke under Admin-menyen i sidefeltet).

### Hva den gjør

* **Laster inn CSV** – dra og slipp eller velg en Agresso-eksportfil (UTF-8 eller Latin-1)
* **Kolonnegjenkjenning** – systemet gjenkjenner automatisk kolonner som `Bilagsdato`, `AV (Konto)`, `Bilagsart`, `Dim 1`, `Beløp` o.l.
* **Kategorisering** – hver transaksjonslinje klassifiseres etter SRS-kategori: **Drift**, **Investering** eller **Gjennomstrømning**
* **Avviksmarkering** – linjer med uventede verdier, manglende dimensjoner eller ukjente bilagsarter flagges med advarselssymbol
* **Sammendrag** – viser antall linjer, totalt beløp, fordeling på kategori og bilagsart

### Kolonnebeskrivelse

| Kolonnenavn | Forklaring |
|-------------|-----------|
| **AV / Konto** | Hovedbokskonto (f.eks. 6000 = lokalkostnader) |
| **Bilagsart** | Transaksjonstype: IV/IW/LE = faktura, H1/H2/HB/RE = ompostering |
| **Dim 1 (Koststed)** | Organisatorisk enhet – brukes til å knytte utgiften til en eiendom |
| **Dim 2 (Prosjekt)** | Prosjekt eller aktivitet |
| **Avgiftstype** | MVA-kode (staten bruker nettoføringsordningen) |
| **BA-kode** | Bedriftsområde / juridisk enhet |

### Slik bruker du den

1. Gå til **`/agresso-csv`**
2. Klikk **«Last opp CSV»** og velg Agresso-filen
3. Gjennomgå sammendragskortet øverst (antall linjer, totalt beløp, kategorifordeling)
4. Se gjennom transaksjonstabellen – **gule rader** er flagget for gjennomgang
5. Bruk **«Kopier prompt»**-knappen for å sende analysen til KI-Kollega for videre vurdering
6. Når filen er validert, importeres den via **Admin → Importer GL-data**

### Vanlige feil

| Problem | Årsak | Løsning |
|---------|-------|---------|
| «Ukjent kolonne» | CSV-header matcher ikke forventet navn | Sjekk at filen er eksportert med standardoppset fra Agresso |
| Alle beløp er 0 | Tusenskilletegn (mellomrom) leses ikke | Systemet renser automatisk, men sjekk desimalskille (komma vs. punktum) |
| Bilagsart «CA/CF/KF/OP» flagget | Utgåtte bilagsarter | Disse skal ikke forekomme i nye uttrekk – kontakt regnskapsavdelingen |
| Mange «Ukategorisert» linjer | Konto finnes ikke i SRS-oversikten | Kontakt superbruker for oppdatering av kontoplan |

---
*Trenger du mer hjelp? Kontakt Superbruker i din region.*
