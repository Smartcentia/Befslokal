# Minnefil: Kostnadsfordeling per eiendom og avdeling

**Formål:** Prosjektminne for arbeid med kostnadsfordeling eiendom ↔ avdeling. Brukes som referanse ved strukturell sjekk og videreutvikling.

**Sist oppdatert:** 3. februar 2026

**Relaterte dokumenter:**
- [STATUS_KOSTNADSFORDELING_AVDELING_EIENDOM.md](STATUS_KOSTNADSFORDELING_AVDELING_EIENDOM.md) – detaljert teknisk status
- [RAPPORT_SISTE_48_TIMER.md](RAPPORT_SISTE_48_TIMER.md) – aktivitetsrapport

---

## 1. Status – kostnadsfordeling per eiendom og avdeling

- **Mål:** Fordele kostnader per eiendom og tilhørende avdeling.
- **Gap:** Det finnes ingen ferdig dimensjon i regnskapet som entydig korrelerer eiendom med riktig avdeling.
- **Tilnærming:** Konvertering/korrelasjonstabell (master_data_crosswalk) som bruker tilgjengelige data (adresse, navn, koder) for å knytte eiendom til avdeling.

---

## 2. Korrelasjonstabell – hva finnes / hva mangler

| Element | Status |
|--------|--------|
| **Tabell og modell** | På plass – `master_data_crosswalk`, `MasterDataCrosswalk` |
| **reconcile_master_data** | Bygger BIRK → PROPERTY (LOCATED_AT), skriver kun til CSV (ikke DB) |
| **GL-import** | Bruker **Dim1 → unit_id_erp** (PASS 0) som første match, deretter learned_mappings, adresse (dim2_name), rebooking, department_name |
| **Dim1 → PROPERTY** | **Implementert:** GL-import mapper Dim1 (department_code) direkte til property_id via property.unit_id_erp (EnhetID fra e-don2). Reconcile lager BIRK → PROPERTY til CSV. |

**Anbefaling:** Fylle crosswalk i DB for andre flater; for GL-import er Dim1 = unit_id_erp brukt som primær kobling.

---

## 2b. Korrelasjon mellom eiendommer – problemstilling

**Problem:** Vi må matche riktig mellom ulike datakilder for å fordele kostnader per eiendom. Korrelasjonen er ikke på plass.

**Datakilder som skal korreleres:**

| Kilde | Identifikator | Nivå |
|-------|---------------|------|
| Eiendomsportfeb.csv | Lokalisering (1101 - FHT…), Avtalenavn, Adresse | Eiendom/kontrakt |
| InnkjøpsanalyseLeie_lokaler m.fl. | Radetiketter (enhetsnavn) | Enhet/avdeling |
| Birk / e-don2 | EnhetID, Navn, adresse | Enhet |
| GL/regnskap | Dim1, dim2_name | Transaksjon |

**Kobling GL → Eiendom (i bruk):** Visma Dim1 = koststedskode = **EnhetID** i ERP = `property.unit_id_erp`. GL-import bruker **Dim1 → unit_id_erp** direkte som første match (PASS 0), deretter adresse og andre fallbacks. birk_og_plasser.csv har Lokasjonskode (BIRK) og EnhetID (= unit_id_erp); eiendommer med `lokalisering_id` og `unit_id_erp` satt (f.eks. 243+) kan dermed kobles uten adresse-matching når e-don2 har fylt data.

**Utfordringer:**
- Eiendom ≠ enhet: én enhet kan ha flere eiendommer; én eiendom kan brukes av flere enheter.
- **Fellesnevner i bruk:** Dim1 (koststed) = EnhetID = property.unit_id_erp – brukes i GL-import (jf. § 26). Adresse-matching brukes som fallback der unit_id_erp mangler.
- Navnematching gir kun ~15 % eksakt + ~26 % delvis (jf. § 11).
- reconcile_master_data bruker portfolio_raw.csv og BIRK – ikke Eiendomsportfeb direkte.
- Crosswalk skrives ikke til DB; GL-import trenger ikke crosswalk for Dim1 fordi unit_id_erp brukes direkte.

**Løsningsveier:**
1. **Bygg mappingstabell ENHET ↔ EIENDOM** – manuelt eller semi-automatisk, basert på dokumentert kunnskap (f.eks. «Røvika Ungdomssenter» bruker eiendom «1104 - Røvika Ungdomssenter»).
2. **Utvid crosswalk** – legg inn INNKJØP_ENHET → PROPERTY (eller BIRK → PROPERTY) og skriv til DB.
3. **Bruk Eiendomsportfeb som portfolio-kilde** – sørg for at reconcile/import leser fra finans/Eiendomsportfeb.csv og matcher mot Lokalisering/Avtalenavn.
4. **e-don2 EnhetID** – hvis Innkjøpsanalyse Radetiketter kan mappes til e-don2 EnhetID, og e-don2 har kobling til eiendom, får vi en indirekte korrelasjon.
5. **Leveringsadresser til Frank Vevle (§ 14)** – filene kobler adresse ↔ enhet (Kontakt). Bruk som bro: match Gateadresse+Postnummer mot Eiendomsportfeb adresse → eiendom; match Kontakt mot Innkjøpsanalyse Radetiketter → enhet. Dermed eiendom ↔ enhet via samme adresse.
6. **bufetat_eiendommer.csv (§ 15)** – Adresse, Kommune, Region, Gnr_Bnr, Eiendomsnummer og Kilde_dokument kan brukes til å mappe opp eiendommer mot Eiendomsportfeb (matrikkel og adresse). Prioriter eiendomsmapping; økonomidata kan overlappe 2025.

**Neste steg:** Prioriter bygging av ENHET↔EIENDOM-mapping (55 matchede + 81 umatchede enheter fra § 11) og integrering i crosswalk/import. Vurdér å bygge mapping via Leveringsadresser (§ 14). Mappe bufetat_eiendommer mot Eiendomsportfeb (§ 15) for entydig eiendomskobling.

---

## 3. Birk / e-don2 – avdeling vs institusjon

- **e-don2** har kolonnene **Enhetskorttype** ("Avdeling", "Barnevernsinstitusjon") og **Enhetstype (Utledet)** (Barnevernsinstitusjon, Institusjonsavdeling, Omsorgssenter).
- **Import** lagrer nå disse ved e-don2-import: **unit_short_type** = Enhetskorttype, **unit_type_derived** = Enhetstype (Utledet) på Property-modellen (jf. § 28).
- **reconcile (Birk)** behandler alle BIRK-enheter likt – ingen skille mellom avdeling og institusjon i reconcile-logikken ennå.

**Anbefaling:** Definer regler for hvilke enheter som skal regnes som avdeling i kostnadsfordeling (f.eks. filtrer på unit_short_type = «Avdeling»). Ved mapping Dim1 → eiendom: bruk EnhetID og hent unit_short_type for avdeling/institusjon.

**Kjøre migrering + e-don2-import (fylle data):** Fra `backend/` med DATABASE_URL satt i `.env`:  
`python scripts/migrer_og_import_edon2_avdeling.py`  
– kjører først alembic upgrade head (legger til unit_short_type, unit_type_derived), deretter e-don2-import slik at matchende eiendommer får satt disse feltene.

---

## 4. Arkiv – KI Kollega og andre funn (kort)

- **ChatInterface** bruker `chatStream` (Avansert), ikke `chatUnified`.
- **chat_unified** bruker Avansert-graf (Supervisor → Researcher → Analyst → Writer), ikke `create_unified_graph` fra unified_agent.
- **Kostnad per kvm:** Bruker fikk svar om «kun Oslo og Viken» – mulig data- eller agent-issue; SCHEMA.md har SQL-eksempler for region-sammenligning.

---

## 5. Struktur for videre sjekk (sjekkliste)

Ved neste gjennomgang, sjekk:

- [ ] **Korrelasjon eiendommer:** ENHET↔EIENDOM-mapping på plass? (jf. § 2b). Mappe bufetat_eiendommer ↔ Eiendomsportfeb (§ 15).
- [ ] **Crosswalk:** Skrives til DB? (reconcile_master_data)
- [x] **GL-import:** Bruker **unit_id_erp** – Dim1 (department_code) mappes direkte til property_id via property.unit_id_erp (PASS 0) før adresse/learned_mappings.
- [ ] **e-don2:** Lagres Enhetskorttype og Enhetstype (Utledet)? **Ja** – unit_short_type og unit_type_derived på Property (jf. § 3, § 28).
- [ ] **Birk:** Skilles avdeling vs institusjon?
- [x] **Dim1:** GL-import matcher regnskapets Dim1 mot property.unit_id_erp (EnhetID fra e-don2).

---

## 6. Relevante filer

| Område | Fil |
|--------|-----|
| Crosswalk-modell | `backend/app/models/master_data_crosswalk.py` |
| Crosswalk-migrasjon | `backend/alembic/versions/8be2957122b1_add_master_data_crosswalk.py` |
| Bygging av koblinger | `backend/scripts/reconcile_master_data.py` |
| GL-import, property-matching | `backend/app/services/data_management.py` (ca. linje 279–330) |
| e-don2-import | `backend/app/services/data_management.py` – `import_edon2_csv` (ca. 455–795) |
| Property-modell | `backend/app/domains/core/models/property.py` |
| Regnregler / Dim1 | `regnregler.md`, `backend/docs/plasseringavavdeling.md`, `backend/docs/ERP_INGEST_SPEC.md` |
| e-don2 kolonner | `backend/e-don2.txt` |
| Eiendomsportfeb (portefølje) | `finans/Eiendomsportfeb.csv` |
| Innkjøpsanalyse leie 2025 (aggregert) | `finans/InnkjøpsanalyseLeie_lokaler 2025.csv` – jf. § 11 |
| Innkjøpsanalyse annen kostnad (aggregert) | `finans/Innkjøpsanalyse_annen_Kostnad.csv` – jf. § 12 |
| Innkjøpsanalyse strøm (aggregert) | `finans/Innkjøpsanalyse_strøm.csv` – jf. § 12 |
| Innkjøpsanalyse agre (aggregert etter kostnadstype) | `finans/Innkjøpsanalyse_agre.csv` – jf. § 13 |
| Leveringsadresser (per region) | `finans/Leveringsadresser til Frank Vevle(Nord).csv` m.fl. – jf. § 14 |
| Bufetat eiendommer | `finans/bufetat_eiendommer.csv` – jf. § 15 |
| Kontraktliste (kontor) | `contracts.csv` / `finans/contracts.csv` – jf. § 16 |
| e-dom (enhetsliste) | `finans/e-dom.txt` – jf. § 17 |
| e-don2 safe | `finans/e-don2_safe.txt`, `backend/e-don2_safe.txt` – jf. § 18 |
| Eie1212 (eiendommer) | `finans/Eie1212.csv` – jf. § 19 |
| Eiendomfebruar (transaksjoner – kun mapping) | `finans/Eiendomfebruar.csv` – jf. § 20. Bruk kun Region/Dim1/Dim2 til mapping; ikke økonomidata. |
| BIRK og plasser (barnevernsinstitusjoner m.m. – kun mapping) | `finans/birk _og_plasser.csv` – jf. § 27. Bruk kun kolonner for eiendomsmapping; ikke plasser/budsjett/personer. |

---

## 7. Eiendomsportfeb.csv – hovedoversikt over kolonner

Kort oversikt over dokumenterte kolonner (kilde: finans/Eiendomsportfeb.csv). Datoformat: norsk (DD.MM.YYYY) som standard.

| Kolonne | Merknad |
|--------|--------|
| Lokalisering | ID + navn (FHT, ESF …). Vurder splitting i to kolonner. |
| Avtalenavn | Kontraktsnavn / eiendomsnavn. Varierer mellom uttrekk. |
| Elements | Dokumentarkiv-kode, unik. Brukes til korrelasjon og berikelse. |
| Tilstandsgrad | Ikke i bruk nå; beholdes for senere. |
| Startdato / Sluttdato | Kontraktsstart og -slutt. |
| Utleier | Motpart i leieavtalen (kan hete Leietaker i andre filer). |
| Utleier kategori | 1 = privat, 2 = offentlig. |
| Hjemmelshaver | Eier i grunnboken. Sjekk om finnes i løsningen. |
| Org.nr / Fnr hjemmelshaver | Brukes til sjekk mot ekstern API. |
| Status | Aktiv / Avsluttet. |
| Poststed, Adresselinje 1 | Finnes under ulike kolonnenavn i andre filer. |
| Lok: Distrikt | Bufetat/Bufdir (f.eks. 01-Nord). |
| Lok: Område | Finere granulering. |
| Type lokasjon | Kontor, Formålsbygg, Familievernkontor m.m. |
| Areal | Kontraktsareal (kan være «450» eller «450 kvm»). |
| Antall godkjente plasser | Kapasitet barn/unge; indikerer barnevern. |
| Målgruppe | Omsorg, Akutt, Behandling høy m.m. (barnevern). |
| Antall årsverk / Antall ansatte | Blanding tall og tekst («se hovedkontrakt»). |
| Antall innleide ansatte | Test; blanding tall/tekst. |
| Byggeår | Kan mangle; kan berikes fra andre kilder. |
| Adresse og Postnummer, Kommunenavn, Fylke | Geografi. |
| Matrikkel Gnr/Bnr/Knr, org nr utleier | Identifikatorer. |
| Areal inkl fellesareal | Format: 924 eller «924 kvm». |
| Eksklusivt areal | Ikke i alle rader. |
| Tillegsareal iht addendum / Reduksjon iht addendum | Blanding tekst og tall (f.eks. «+ 122 kvm fra 01.01.2022»). |
| Tomteareal | Tomtestørrelse der relevant. |
| Leieregulering | KPI-andel leie/vedlikehold (f.eks. «100% av KPI på leie»). |
| Adgang til forlengelse og vilkår | JA + varslingsfrist (f.eks. min 6/9 mnd før utløp). |
| P-plasser | Blanding tall og tekst (antall, inkl, betalingsregler). |
| Kontraktsleie ved oppstart (per år) | Blanding tall og tekst (f.eks. «4025842 etter reduksjon av hytte i 2013»). |
| Kontraktsleie økning/reduksjon | Tekst (f.eks. «økes med 234000,- fra 01.01.2017»). |
| Oppstartsdato (KPI-grunnlag) – Gyldig kontrakt | Dato; kan være amerikansk format – normaliser til norsk. |
| Kontraktsleie ved oppstart (gyldig kontrakt) | Blanding tall og tekst (f.eks. «Ny kontrakt fra 01.01.2026»). |
| KPI-justert kontraktsleie til okt 2025 | Samme mønster; kan inneholde tekstrader. |
| Indre vedlikehold | Blanding tall og tekst. |
| KPI-justert indre vedlikehold | Samme. |
| Indre vedlikehold pr/kvm | Tall (f.eks. 60, 70, 148); hensikt usikker. |
| Felleskostnader per år (ved kontraktsinngåelse) | Tall; ikke alle eiendommer har verdi. |
| Brukeravhengige driftskostnader – Første driftsår | Kan ha tomme verdier. |
| KPI-justert: Brukeravhengige driftskostnader | Tall. |
| Kostnader: kommunale gebyrer og renovasjon | Mange tomme – ofte pakket inn i leie/årsleie. |
| Kost kortleser | Samme – mange uten verdi. |
| Parkeringsleie kr per år | Kun for utvalgte eiendommer. |
| **Merverdikompensasjon per år** | Årlig beløp; mange tomme. Refusjon MVA – jf. § 9 under. |
| Vaktmestertjenester kr per år | Kun for et fåtall eiendommer. |
| Energi til leieobjektet kr per år | Kun for et fåtall; kan estimeres for alle – jf. § 10. |
| Oppvarming pr år | Ingen data i filen; kan korreleres med Energi – jf. § 10 (splitt varme vs. rest). |
| Renhold pr år | Ingen data nå; skal fylles senere. |
| Kontantinnskudd kr | Brukes lite; blanding tall og tekst. Se nedenfor for typer. |
| Betaling administrativt arbeid Statsbygg | Kun for noen eiendommer. |
| kommentar | Kun tekst (fritekst). |

**Kontantinnskudd kr – mulige betydninger:** (1) **Sikkerhet/depositum** – beløp på sperret konto som sikkerhet for leieavtalen (ofte tilsvarer 3 eller 6 mnd leie). (2) **Investeringstilskudd** – engangsbeløp fra leietaker for at utleier tilpasser lokalene. (3) **Andel i fellesanlegg** – innskudd for tilgang til felles infrastruktur (f.eks. stasjonsbygninger). Rundt tall (f.eks. 50 000 kr) tyder ofte på depositum.

---

## 8. Eiendomsportfeb.csv – kolonne: Merverdikompensasjon per år

**Kolonnenavn:** Merverdikompensasjon per år  

**Innhold:** Årlig beløp for merverdiavgiftskompensasjon knyttet til eiendommen/avtalen. Kan være tom for mange eiendommer (avtale-/bruksavhengig).

**Hensikt i minne:** Ved tolkning av tall og rapportering – vite at dette er refusjon/kompensasjon fra staten for betalt MVA, ikke en egen avgift.

---

## 9. Merverdikompensasjon – hvordan beregnes det (offentlig sektor)

Kilde: [Merverdiavgiftskompensasjonsloven](https://lovdata.no/dokument/NL/lov/2003-12-12-108) (lov 2003-12-12-108), Skatteetaten (M-23).

- **Formål:** Motvirke konkurransevridning fordi offentlige virksomheter ikke kan trekke fra inngående MVA som private.
- **Hvem:** Kommuner, fylkeskommuner, interkommunale selskap, barnehager, kirkelig fellesråd, ideelle organisasjoner m.fl. (§ 2).
- **Hva kompenseres (§ 3):** Merverdiavgift ved kjøp av varer og tjenester fra registrerte næringsdrivende, samt MVA ved innførsel og kjøp av tjenester fra utlandet/Svalbard/Jan Mayen.
- **Beregning:** Det ytes kompensasjon for **faktisk betalt MVA** på anskaffelser som skjer til bruk i den kompensasjonsberettigede virksomheten. Det finnes ikke én fast prosent – kompensasjonen tilsvarer den MVA som er betalt og som loven åpner for å refundere.
- **Begrensninger (§ 4):** Bare til bruk i kompensasjonsberettiget virksomhet; ikke for MVA der det allerede er fradragsrett; ikke for anskaffelser til bygg/anlegg til salg eller utleie (unntak f.eks. internat); ikke for anskaffelser ≥ 10 000 kr som ikke er betalt via bank.
- **Beløpsgrense (§ 6):** Krav kan ikke fremsettes før de samlede MVA-kostnadene i et kalenderår utgjør minst 20 000 kr.
- **Utleie til offentlig:** Ved utleie til kommuner/fylkeskommuner til kompensasjonsberettiget bruk kan utleier ha rett til frivillig MVA-registrering (Skatteetaten M-2-3.3), slik at leietaker i praksis får refusjon for MVA-delen i leien.

**Konklusjon for databruk:** Kolonnen «Merverdikompensasjon per år» i Eiendomsportfeb.csv er et årlig beløp (refusjon/estimat). Det er ikke en egen formel i porteføljedata – selve beregningen følger lov og forskrift og gjøres i skattemelding/regnsystem; kolonnen viser resultatet per avtale/eiendom.

---

## 10. Energi til leieobjektet – estimert beregning for alle eiendommer

**Plan:** Sjekke og beregne estimert energikostnad for alle eiendommer i Eiendomsportfeb.csv, der kolonnen «Energi til leieobjektet kr per år» ofte er tom. Kun én eiendom (Ole Tobias Olsens gate 19) har faktisk verdi i eksempel (48 400 kr/år for 154 kvm).

**Nødvendig input:**
- **Areal (m²):** Areal / Areal inkl fellesareal – finnes for de fleste
- **Byggeår:** Byggeår – kan mangle; kan berikes fra andre kilder
- **Prisområde (NO1–NO5):** Fylke / Kommunenavn – kan mappes til NO-soner

**Beregningsmodell:**

1. **kWh/m²** ut fra byggeår (eller bygningstype):
   - Eldre bygg: 250–350 kWh/m²
   - Nyere/renovert: 200–250 kWh/m²
   - TEK17/nybygg: 150–200 kWh/m²

2. **Strømpris (kr/kWh)** ut fra prisområde:
   - NO4 (Nord-Norge, f.eks. Mo i Rana): 1,50–1,80 kr/kWh
   - NO1 (Oslo): høyere
   - NO2, NO3, NO5: egne intervaller

3. **Årlig kostnad** = areal × kWh/m² × kr/kWh

**Referanseberegning (Ole Tobias Olsens gate 19, 154 kvm, eldre bygg i Mo i Rana/NO4):**

| Scenario | Forbruk (kWh) | Pris per kWh | Årlig kostnad |
|----------|---------------|--------------|----------------|
| Gunstig | 38 500 | 1,50 kr | 57 750 kr |
| Normalt | 45 000 | 1,65 kr | 74 250 kr |
| Høyt | 53 900 | 1,80 kr | 97 020 kr |

*Faktisk verdi i data: 48 400 kr – lavere enn gunstig; mulig lavere pris eller forbruk.*

**Oppvarming pr år – korrelasjon med Energi og splitt varme vs. rest**

Kolonnen «Oppvarming pr år» har ingen data i filen, men kan knyttes til «Energi til leieobjektet kr per år»: når vi har estimert eller faktisk forbruk til oppvarming (kWh), kan resten av strømkostnaden estimeres.

*Typisk fordeling (norsk bolig – andeler kan avvike for næringsbygg/kontor):*

| Post | Andel av totalt strømforbruk |
|------|------------------------------|
| Oppvarming | ca. 60–70 % |
| Varmtvann | ca. 15–20 % |
| Lys og elektriske apparater | ca. 15 % |

*Restforbruk (utenom oppvarming) – erfaringsstall for 154 kvm:*
- **Varmtvann:** 2 500–5 000 kWh/år (avhenger av antall personer)
- **Lys og apparater:** 4 000–6 000 kWh/år
- **Elbillading (valgfritt):** 2 500–3 500 kWh/år

*Formel:* Total strømkostnad = (Varme_kWh + Vann_kWh + Apparater_kWh) × Pris_per_kWh  

*Eksempel (uten oppvarming):* Varmtvann 4 500 kWh + Lys/apparater 5 000 kWh = 9 500 kWh; ved 2,00 kr/kWh → ca. 19 000 kr/år for «resten».

For næringsbygg (kontor, formålsbygg) kan andelene være andre (mer lys/IT, mindre andel oppvarming i nyere bygg).

**Gjennomføring:** Ikke implementert ennå. Skal kjøres ved senere anledning.

---

## 11. InnkjøpsanalyseLeie_lokaler 2025.csv – aggregerte data 2025

**Fil:** `finans/InnkjøpsanalyseLeie_lokaler 2025.csv`  
**Innhold:** Aggregerte innkjøpsdata for leie av lokaler og tilknyttede kostnader, per enhet/avdeling og per region (Bufetat) og Bufdir-totalsum. Semikolon som separator.

**Metadata (topp av fil, rad 1–9):**

| Rad | Felt | Eksempel/innhold |
|-----|------|-------------------|
| 3 | Periodekalender | 2025 |
| 4 | Kapittel Beskrivelse | All |
| 5 | Kontonummer | (Flere elementer) |
| 7 | Kontantbeløp / Kolonneetiketter | Overskrift |
| 8 | Bufetat / Bufdir / Totalsum | Kolonnegrupper |
| 9 | Radetiketter + regioner | Faktiske kolonnenavn |

**Kolonner (fra rad 9):**

| Kolonne | Beskrivelse |
|---------|-------------|
| Radetiketter | Enhet/avdeling (f.eks. Agder barne- og familiesenter, Regionkontor, MST Bodø). |
| Region Midt-Norge | Kontantbeløp (kr) for region Midt-Norge. |
| Region Nord | Kontantbeløp (kr) for region Nord. |
| Region Sør | Kontantbeløp (kr) for region Sør. |
| Region Vest | Kontantbeløp (kr) for region Vest. |
| Region Øst | Kontantbeløp (kr) for region Øst. |
| (kolonne 7–8) | Tomme eller mellomsummer i noen rader. |
| Totalsum | Sum kontantbeløp for raden (siste tallkolonne). |

**Radinndeling / kapittel (hierarki i filen):**

Filen er inndelt i rader etter kostnadstype. Under hver gruppe kommer rader med enhetsnavn og beløp fordelt på regioner.

1. Leie av lokaler og tilknyttede utgifter (overordnet)  
2. Leie lokaler andre utleiere  
3. Leie lokaler fra Statsbygg  
4. Fellesutgifter (BAD) Statsbygg  
5. Fellesutgifter andre utleiere  
6. Strøm og oppvarming  
7. Renhold lokaler  
8. Reparasjon og vedlikehold leide lokaler  
9. Annen kostnad lokaler  
10. Fellesutgifter Statsbygg - indre vedlikehold  
11. Leie parkeringsplass  
12. Vakthold lokaler  
13. Vaktmestertjenester  
14. Renovasjon, vann, avløp o.l.  
15. Reparasjon og vedlikehold av anlegg, også serviceavtaler  
16. Fast bygningsinventar over kr 50 000  

**Datastruktur:** En rad er enten en kapitteloverskrift (kun tekst i kolonne 1, resten tomt) eller en enhetsrad (enhetsnavn i kolonne 1, beløp i regionkolonnene og totalsum). Beløp med mellomrom (f.eks. «  28 488 729») må parses til tall. Siste datarad er ofte «Totalsum» med region- og totalsummer.

**Korreliasjon:** Radetiketter (enhetsnavn) kan brukes til å knytte mot Eiendomsportfeb.csv og e-don2 (avdeling/enhet) ved navnematching eller crosswalk.

**Korrelasjonssjekk Radetiketter vs Eiendomsportfeb (Lokalisering/Avtalenavn):**

| Resultat | Antall | Andel |
|----------|--------|-------|
| Eksakt match | 20 | 14,7 % |
| Delvis match | 35 | 25,7 % |
| Ingen match | 81 | 59,6 % |
| **Totalt unike enheter i Innkjøpsanalyse** | **136** | |

*Eksempler eksakt match:* Røvika Ungdomssenter, Alta Ungdomssenter, Bodø Familievernkontor, Sollia barne- og ungdomssenter, Viktoria Familiesenter.  
*Eksempler delvis match:* Bodø behandlingssenter ↔ Bodø Behandlingssenter (i kjøpsprosess); Barkåker ungdomssenter ↔ Barkåker.  
*Ingen match:* Enheter som Agder barne- og familiesenter, FHT region nord, Enhet for inntak (Bufetat region …), Kontorfaglig enhet – disse er ofte aggregerte eller har andre navn i porteføljen.

**Konklusjon:** Navnematching gir begrenset dekning. For bedre korrelasjon: bruk crosswalk (master_data_crosswalk) eller e-don2 med EnhetID/Enhetsnavn, eller bygg mappingstabell enhet ↔ eiendom.

**Registrert i minne – enheter med match mot Eiendomsportfeb (55 stk):**

*Eksakt match (20):* Alta Ungdomssenter · Bodø Familievernkontor · Clausenengen ungdomshjem · Eikelund Ungdomssenter · Familievernkontoret Asker og Bærum · Familievernkontoret Oslo Nord · Humla Akuttsenter · Innlandet barnevernsenter · Karienborg ungdomsheim · Lunde behandlingssenter · Ranheim Vestre · Røvika Ungdomssenter · Seljelia barne- og familiesenter · Solbakken Barne- og familiesenter · Sollia barne- og ungdomssenter · Stokke Barnesenter · Sundstedtråkka ungdomssenter akutt · Tromsø ungdomssenter · Vikhovlia akuttsenter · Viktoria Familiesenter

*Delvis match (35):* Akershus ungdoms- og familiesenter ↔ avdeling Børlien · Barkåker ungdomssenter ↔ Barkåker · Bjørgvin Ungdomssenter ↔ Bjørgvin Bønnesstølen · Bodø behandlingssenter ↔ Bodø Behandlingssenter (i kjøpsprosess) · Borg barne- og familiesenter ↔ avdeling Moringen · Familievernkontoret Enerhaugen ↔ Grønlandsleiret · Familievernkontoret Innlandet Vest ↔ Gjøvik · Familievernkontoret Innlandet Øst ↔ avdeling Tynset · Familievernkontoret Ålesund · Familievernkontoret Østfold · Finnsnes Familievernkontor · Fosterhjemstjenesten (region vest, midt, sør, øst) · Gilantunet ungdomshjem ↔ (oppsagt) · Grøterød ungdomshjem ↔ Grøterød · Husafjellheimen ungdomsheim ↔ Husafjellheimen · Justøya behandling ungdom ↔ Justøy · Katfoss behandling ungdom ↔ Katfoss · Kirkenær barnevern- og omsorgssenter ↔ Edda · Klokkerhuset ungdomssenter akutt ↔ Klokkerhuset · Kollen ungdomsbase ↔ Vestnes · Lågen ungdomshjem ↔ Lågen · Nye Kvæfjord ungdomssenter ↔ Kvæfjord Ungdomssenter · Nye Lamo ungdomssenter ↔ Lamo Ungdomssenter · Regionale utgifter (regionkontor,fellestjenester) · Regionkontor ↔ Pirsenteret · Ringerike omsorgssenter ↔ avdeling administrasjon · Sandnes Ungdomssenter ↔ Minde 1 + Minde 2 · Silsand ungdomssenter ↔ Islandsbotnveien 35 · Skjerven rusbehandling ungdom ↔ Skjerven · Sogndal Ungdomssenter ↔ Rødstokken · Stavanger ungdomssenter ↔ Våland · Thorøya ungdomshjem ↔ Thorøya

---

**Registrert i minne – enheter uten match mot Eiendomsportfeb (81 stk):**

Full liste:

Adferdssenter Ungdom · Agder barne- og familiesenter · Agder ungdomshjem · Agder ungdomssenter · Akershus ungdoms- og familiesenter - akutt · Alta / Hammerfest FV · Avdelingsdirektør inntak og fosterhjemsrekruttering · Avdelingsdirektør omsorg for ungdom og behandling av ungdom · Bergen Akuttsenter Ungdom · Bufetats behandlingssenter Akershus_Østfold · Buskerud barne- og familiesenter · Enhet for inntak, Bufetat region midt · Enhet for inntak, Bufetat region nord · Enhet for inntak, Bufetat region sør · Enhet for inntak, Bufetat region øst · Enhet for spesialiserte fosterhjem · Enhet for spesialiserte fosterhjem - region øst · FHT region nord · Familiehjem i region vest · Familiekontora for Sunnfjord og Sogn · Familievernets spisskompetansemiljø for vold og høykonflikt · Familievernkontorene Drammen-Kongsberg · Familievernkontoret Homansbyen · Familievernkontoret Kristiansund · Familievernkontoret Levanger · Familievernkontoret Molde · Familievernkontoret Namsos · Familievernkontoret Nedre Romerike · Familievernkontoret for Bergen og omland · Familievernkontoret i Vestfold · Familievernkontoret Øvre Romerike Glåmdalen · Gullhella barne- og familiesenter · Harstad / Narvik FV · Hedmark ungdoms- og familiesenter - akutt · Indre Finnmark Familievernkontor · Jong ungdoms- og familiesenter · Kasa Ungdomssenter · Kontorfaglig enhet · Kvammen akuttinstitusjon · Lierfoss ungdoms- og familiesenter - omsorg · MST Bodø · MST Mo i Rana · MST Sunnmøre · MST Tromsø · MST Trøndelag Nord · MST region sør · Multisystemisk terapi-team Gjøvik · Multisystemisk terapi-team Hamar · Multisystemisk terapi-team Lillestrøm · Multisystemisk terapi-team Sarpsborg · Multisystemisk terapi-team Ski · Multisystemisk terapi-team Sandvika · Nasjonal enhet for behandlingstiltak · Nasjonal enhet for godkjenning og etterfølgende kontroll av private institusjoner · Nasjonalt samisk kompetansesenter · Region vest senter for foreldre og barn · Regionale felleskostnader · Regiondirektøren · Regionkontoret frikjøpte (tillitsvalgt osv) · Seksjon adopsjon · Senter for foreldre og barn Molde · Skjoldvegen barnevernsenter · Sogn og Fjordane ungdomsenter · Sogn og fjordane Ungdomssenter behandling høy · Spesialiserte fosterhjem · Spillumheimen undomsheim · St. Hansgården ungdomssenter akutt · Stab · Stavanger Akuttsenter Ungdom · Sunnmørsheimen akuttsenter · Sunnmørsheimen ungdomsheim · Teknisk · Telemark barne- og familiesenter · Telemark og Vestfold ungdomshjem · Tromsø Familievernkontor · Trøndelag behandlingssenter for ungdom · Vesterålen Familievernkontor · Vestfold barne- og familiesenter · Vestfold ungdomssenter · Yttrabekken Ungdomshjem · Østfold ungdoms- og familiesenter - omsorg

---

## 12. Innkjøpsanalyse_annen_Kostnad.csv og Innkjøpsanalyse_strøm.csv – samme inndeling

**Filer:**  
- `finans/Innkjøpsanalyse_annen_Kostnad.csv` – Annen kostnad lokaler  
- `finans/Innkjøpsanalyse_strøm.csv` – Strøm og oppvarming  

**Innhold:** Aggregerte innkjøpsdata opp til eiendom. **Samme datastruktur** – radene er gruppert etter region, ikke kolonner (annerledes enn InnkjøpsanalyseLeie_lokaler).

**Metadata (topp):** Periodekalender 2025, Kapittel All. Konto Beskrivelse varierer per fil («Annen kostnad lokaler» / «Strøm og oppvarming»).

**Kolonner:**

| Kolonne | Beskrivelse |
|---------|-------------|
| Radetiketter | Region-navn (Region Sør, Region Midt-Norge …) eller enhetsnavn. |
| Kontantbeløp | Beløp (kr) for raden. |

**Radinndeling – gruppert under Bufetat:**

Radenes rekkefølge er hierarkisk. Først kommer overordnede overskrifter, deretter regioner med enheter under hver:

1. Leie av lokaler og tilknyttede utgifter  
2. Bufetat  
3. **Region Sør** → enheter med beløp  
4. **Region Midt-Norge** → enheter med beløp  
5. **Region Øst** → enheter med beløp  
6. **Region Nord** → enheter med beløp  
7. **Region Vest** → enheter med beløp  
8. **Bufdir** → (evt. mellomsum)  
9. Totalsum  

**Forskjell fra InnkjøpsanalyseLeie_lokaler (§ 11):**  
- *Leie_lokaler:* Kolonner = regioner (Region Midt-Norge, Nord, Sør, Vest, Øst, Bufdir, Totalsum). Hver rad = én enhet med beløp per region.  
- *Annen_Kostnad / Strøm:* Radene er gruppert etter region. Radetiketter = region-navn eller enhetsnavn. Kun én Kontantbeløp-kolonne. Enhetene ligger under hver region-seksjon.

---

## 13. Innkjøpsanalyse_agre.csv – aggregert etter kostnadstype

**Fil:** `finans/Innkjøpsanalyse_agre.csv`  
**Innhold:** Trolig aggregert fra de andre innkjøpsanalyse-filene. **Radetiketter = kostnadskategorier** (ikke enheter). Samme kolonneoppsett som InnkjøpsanalyseLeie_lokaler (regioner som kolonner).

**Kolonner:** Radetiketter | Region Midt-Norge | Region Nord | Region Sør | Region Vest | Region Øst | (tom) | Bufdir | Totalsum.

**Radetiketter (kostnadskategorier):**

- Leie av lokaler og tilknyttede utgifter (overordnet)
- Leie lokaler andre utleiere · Leie lokaler fra Statsbygg · Fellesutgifter (BAD) Statsbygg · Fellesutgifter andre utleiere · Strøm og oppvarming · Renhold lokaler · Reparasjon og vedlikehold leide lokaler · Annen kostnad lokaler · Leie parkeringsplass · Vakthold lokaler · Vaktmestertjenester · Renovasjon, vann, avløp o.l. · Reparasjon og vedlikehold av anlegg, også serviceavtaler
- **Kontor og administrasjon** (overordnet)
- Reparasjon og vedlikehold av verktøy og maskiner, inkl serviceavtaler
- **IKT** (overordnet)
- Reparasjon og vedlikehold av datautstyr, inkl. serviceavtaler
- Totalsum

**Sammenligning med andre filer:** Radene i agre tilsvarer kapittel/kostnadstype fra Leie_lokaler (§ 11) pluss Kontor og administrasjon / IKT. Tall per rad og region bør kunne sjekkes mot sum av enhetsrader i Leie_lokaler for samme kostnadstype. Totalsum agre (497 471 735) avviker noe fra Totalsum i Leie_lokaler (504 079 834) – ulik scope eller tidsavsnitt.

---

## 14. Leveringsadresser til Frank Vevle – per region

**Filer (6 stk):**

| Fil | Region |
|-----|--------|
| `finans/Leveringsadresser til Frank Vevle(Nord).csv` | Nord |
| `finans/Leveringsadresser til Frank Vevle(Midt).csv` | Midt-Norge |
| `finans/Leveringsadresser til Frank Vevle(Sør).csv` | Sør |
| `finans/Leveringsadresser til Frank Vevle(Vest).csv` | Vest |
| `finans/Leveringsadresser til Frank Vevle(Øst).csv` | Øst |
| `finans/Leveringsadresser til Frank Vevle(Bufdir).csv` | Bufdir |

**Kolonner:** Gateadresse | Poststed | Postnummer | Kontakt.

- **Gateadresse:** Adresse, ofte med bygg/etg eller enhetsbetegnelse (f.eks. «Nordstrandveien 41, 5. etg Stab - Bodø», «Ole Tobias Olsensgt. 19»).
- **Poststed, Postnummer:** Geografi.
- **Kontakt:** Enhetsnavn / avdelingsnavn (f.eks. «MST Mo i Rana», «Røvika ungdomssenter», «Bodø FVK», «Klokkerhuset»).

**Bruk til mapping:** Filene kobler **adresse ↔ enhet (Kontakt)**. De kan brukes til korrelasjon:

1. **Leveringsadresser (Gateadresse + Postnummer)** ↔ **Eiendomsportfeb (Adresse og Postnummer / Adresselinje 1)**  
   Normalisert adresse-match gir eiendom fra porteføljen.

2. **Leveringsadresser (Kontakt)** ↔ **Innkjøpsanalyse (Radetiketter)**  
   Kontakt er enhetsnavn; kan matches mot Radetiketter (evt. normalisert).

3. **Kjede for eiendom ↔ enhet:**  
   Eiendomsportfeb (eiendom, adresse) ← adresse ← Leveringsadresser (adresse, Kontakt) → Kontakt → Innkjøpsanalyse (enhet).  
   Dermed: **Leveringsadresser som bro mellom eiendom og enhet** – bruk samme adresse til å knytte Eiendomsportfeb til Innkjøpsanalyse via Kontakt/Radetiketter.

**Merk:** Gateadresse kan inneholde etasje/avdeling; ved matching mot Eiendomsportfeb bør kun gate + postnummer (evt. poststed) brukes eller normaliseres slik at bygg uten etasje også matcher.

---

## 15. bufetat_eiendommer.csv – mapping av eiendommer

**Fil:** `finans/bufetat_eiendommer.csv`  
**Rader:** 48 datarader (+ header).  
**Viktig:** Det kan være overlappende økonomidata for 2025 med Eiendomsportfeb og Innkjøpsanalyse; **prioritet er å mappe opp eiendommer** (korrelere rader til samme eiendom i Eiendomsportfeb/portefølje).

**Kolonner:**

| Kolonne | Beskrivelse |
|---------|-------------|
| ID | Rad-ID. |
| Adresse | Adresse (kan være postboks, gate, stedsnavn). |
| Kommune | Kommunenavn. |
| Region | Vest, Sør, Nord, Øst, Midt-norge. |
| Gnr_Bnr | Gårdsnummer/Bruksnummer (matrikkel). |
| Eiendomsnummer | Eiendomsnummer (f.eks. 13854, 13916). |
| BTA_m2 | Bruttoareal m². |
| Tomteareal_m2 | Tomteareal m². |
| Byggeår | Byggeår. |
| Årlig_leie_kr, Månedlig_leie_kr, Leie_per_m2_år | Leie – ofte rene tall (overlapp med Eiendomsportfeb 2025). |
| Vedlikeholdsavgift_kr, Driftsutgifter_kr | Vedlikehold og driftskostnader. |
| Parkeringsplasser, Parkering_type, Elbil_lading, Parkering_kostnad_kr | Parkering. |
| Institusjonstype | F.eks. Ungdomshjem, Behandlingssenter. |
| Energikarakter, Oppvarming, Heis | Bygningsstandard – nytt for berikelse. |
| Kontrakt_fra, Kontrakt_til, Leieperiode, Oppsigelse_måneder | Kontraktsperiode. |
| Statsbygg | Ja/blank – om Statsbygg er utleier. |
| Kilde_dokument | PDF-filnavn – sporing til kontrakt. |

**Mapping til andre kilder:**
- **Adresse + Kommune/Region** → match mot Eiendomsportfeb «Adresse og Postnummer» / Adresselinje 1 og Lok: Distrikt/Område.
- **Gnr_Bnr, Eiendomsnummer** → match mot Eiendomsportfeb Matrikkel Gnr, Bnr, Knr og eventuell eiendoms-ID. Sterk for entydig eiendomskobling.
- **Kilde_dokument** → kan inneholde adresse eller objektnavn (f.eks. «Lagaårdsveien 44 (Bufetathus Stavanger)») – bruk til å utlede eller verifisere eiendom.

**Kjørt mapping (script `finans/map_bufetat_to_portfeb.py`):** Match på Gnr_Bnr og normalisert adresse (token-overlap) mot Eiendomsportfeb. Resultat: **22 bufetat-rader** har minst én match til Eiendomsportfeb; **19 unike Eiendomsportfeb-eiendommer** er mappet; **26 unike (bufetat_rad, portfeb_lok)-par**. 18 matcher på Gnr_Bnr, 15 på adresse (noen adressematcher kan være feilpositive – f.eks. samme gatenavn ulike steder). 26 bufetat-rader umappet (bl.a. Postboks, kun Kilde_dokument uten adresse, eller adresse som ikke finnes i portfeb).

**Overlapp økonomi 2025:** Årlig_leie_kr, Vedlikeholdsavgift_kr, Driftsutgifter_kr osv. kan overlappe med Eiendomsportfeb og Innkjøpsanalyse. Ved sammenligning bruk eiendomsmapping først, deretter sammenlign beløp per matchet eiendom.

---

## 16. contracts.csv – kontraktliste (kontor)

**Fil:** `contracts.csv` / `finans/contracts.csv` (samme innhold).  
**Rader:** 159 (1 header + 158 datarader).

**Kolonner:**

| Kolonne | Beskrivelse |
|---------|-------------|
| # | Radnummer. |
| Region | Vest, Nord, Øst, Sør, Midt. |
| Filnavn (Kilde) | Kort filnavn/referanse til kontraktdokument (avkortet). |
| Kontraktnr | Kontraktsnummer (f.eks. 8323, 13916, 11509) – kan matche Eiendomsnummer/Kilde i andre filer. |
| Kategori | Leieavtale, Leiekontrakt, Addendum, Tillegg, Opphør, Kravspes., Fil mangler, Ny i finansliste, m.fl. |
| Adresse | Full adresse (gate, sted). |
| Type Lokale | Kontor, Bolig, Institusjon, Bolig/Inst., Næring, Lager/Ktr, m.fl. |
| Areal (m²) | Areal – tall eller tekst (f.eks. "2 rom", "Flere"); noen rader har tall i feil kolonne (147–149). |
| Gnr/Bnr | Matrikkel (f.eks. 37/237, 47/384, 44/54) – direkte match mot Eiendomsportfeb og bufetat_eiendommer. |
| Status (01.01.26) | 🔴 UTLØPT, 🟢 Aktiv, ⚪ Ukjent, ❓ Sjekk, ⚫ Opphørt. |
| Startdato, Sluttdato, Varighet | Kontraktsperiode. |
| Oppsigelse / Klausuler | Varsel, uoppsigelig, tidsbestemt, m.m. |
| Opsjon / Forlengelse | Opsjon, forlengelse, reforhandling. |
| Parkering / Garasje | Beskrivelse av parkering. |
| Fasiliteter / Teknisk / Ute | Ekstra fasiliteter. |
| Signert Dato, Opprettet Dato | Datoer (ulike formater). |

**Bruk til mapping:** Adresse, Gnr/Bnr og Kontraktnr kan brukes til å knytte contracts.csv mot Eiendomsportfeb og bufetat_eiendommer. Region tilsvarer geografisk inndeling. Filnavn (Kilde) kan brukes til å koble til PDF/kontraktarkiv.

**Kjørt mapping (script `finans/map_contracts_to_portfeb.py`):** Match på Gnr/Bnr og normalisert adresse (token-overlap) mot Eiendomsportfeb. Resultat: **135 contract-rader** har minst én match; **103 unike Eiendomsportfeb-eiendommer** er mappet; **172 unike (contract_rad, portfeb_lok)-par**. 79 matcher på Gnr/Bnr, 129 på adresse (overlap mulig). 24 contract-rader umappet (mange uten Gnr/Bnr: kun stedsnavn, «Fil mangler», eller spesiell radstruktur som rader 150–153 «Ny i finansliste»).

---

## 17. e-dom.txt – enhetsliste (e-don2-lignende)

**Fil:** `finans/e-dom.txt`  
**Format:** Tab-separert (TSV). Første linje er introduksjon («jeg gir deg alle dataene :») deretter kolonnenavn som header.  
**Innhold:** Enhetsregister-lignende data for barnevernsinstitusjoner og avdelinger – tilsvarer e-don2-struktur (EnhetID, Enhetsnavn, adresse, type).

**Kolonner (fra header):**

| Kolonne | Beskrivelse |
|---------|-------------|
| Region | Midt, Øst, Vest, Sør, Nord. |
| Tilhørighet2EnhetID, Tilhørighet2 | Overordnet enhet (ID og navn). |
| TilhørighetEnhetID, Tilhørighet | Nærmere tilhørighet (institusjon/regionenhet). |
| EnhetID | Unik enhets-ID (tall, f.eks. 1901, 2411, 38710). |
| Enhetsnavn | Navn på enheten (f.eks. «Kvalvågveien Boenhet», «Rødstokken»). |
| Enhetskorttype | Avdeling, Barnevernsinstitusjon. |
| Enhetstype (Utledet) | Barnevernsinstitusjon, Institusjonsavdeling, Omsorgssenter. |
| Antall G/K - plasser, Antall budsjetterte plasser | Kapasitet. |
| Hjemler | Lovparagrafer (§ 4-2, § 5-1, m.fl.). |
| Nedlagt Dato | Tom eller dato. |
| Eierskapenhet | Statlig, Kommunal, Privat ideell, Privat kommersiell. |
| Lokasjonskode, ePhorte Adm Id | Koder. |
| Fylke, Kommune | Geografi. |
| Adresse, Postnummer, Poststed | Full adresse. |
| Telefon, Nettside, EPost, Orgnr | Kontakt og org.nr. |

**Bruk til mapping:** EnhetID og Enhetsnavn kan matches mot Innkjøpsanalyse Radetiketter og Leveringsadresser Kontakt. Adresse + Postnummer kan matches mot Eiendomsportfeb og contracts.csv for eiendom ↔ enhet-kobling. Tilsvarer typen data som e-don2-import bruker – nyttig for korrelasjon ENHET ↔ EIENDOM (jf. § 2b).

**Kjørt mapping (script `finans/map_edom_to_portfeb.py`):** Match på adresse+postnummer og Enhetsnavn (token-overlap) mot Eiendomsportfeb. Resultat: **11 e-dom-rader** har minst én match; **9 unike Eiendomsportfeb-eiendommer** mappet; **11 unike (e-dom enhet, portfeb)-par**. 7 matcher på adresse, 5 på navn (noen navnematcher kan være feilpositive). 129 e-dom-rader umappet – mange er avdelinger/boenheter som ikke har egen eiendom i porteføljen.

---

## 18. e-don2_safe.txt

**Filer:** `finans/e-don2_safe.txt`, `backend/e-don2_safe.txt`  
**Status:** Begge filene inneholder foreløpig **kun én linje** med plassholdertekst (`%SAME% (I will use the content from the previous tool)`). Det er altså ikke reell enhetsdata i disse filene per i dag.

**Hensikt:** «Safe»-variant av e-don2 – sannsynligvis tenkt som anonymisert eller sikker kopi med samme kolonnestruktur som e-don2/e-dom (jf. § 17 og `backend/e-don2.txt`).

**Bruk:** For faktisk e-don2-enhetsdata, bruk **e-dom.txt** (finans) eller **backend/e-don2.txt** (ren TSV, 1 header + 476 datarader). Kolonnene er de samme som i § 17 (Region, EnhetID, Enhetsnavn, Enhetskorttype, Enhetstype (Utledet), Adresse, Postnummer, Poststed, m.fl.).

---

## 19. Eie1212.csv – bruk kun til mapping av eiendommer

**Fil:** `finans/Eie1212.csv`  
**Format:** Semikolon-separert (;). Evt. BOM på første kolonne.  
**Rader:** 249 (1 header + 248 datarader).

**Viktig:** Bruk **kun** denne filen til å mappe opp eiendommer (identifikatorer, adresse, matrikkel). **Ikke bruk økonomitallene** – kolonnene for leie, vedlikehold, felleskostnader m.m. skal ikke benyttes som kilde til beløp.

**Kolonner relevante for eiendomsmapping (bruk disse):**

| Kolonne | Bruk til mapping |
|---------|-------------------|
| Lokalisering | Eiendoms-ID/lokalisering (f.eks. «3501 - KASA Sandsli», «4715 - Tovdal»). Primær nøkkel mot Eiendomsportfeb. |
| Avtalenavn | Avtalenavn / enhetsnavn. |
| Adresselinje 1 | Gateadresse. |
| Adresse og Postnummer | Full adresse inkl. postnummer og poststed. |
| Poststed, kommunenavn, Fylke | Geografi. |
| Matrikkel Gnr, Matrikkel Bnr, Matrikkel Knr | Matrikkel – match mot Eiendomsportfeb, contracts, bufetat_eiendommer. |
| Type lokasjon, Areal | Bygning/areal (valgfritt for validering). |

**Kolonner som er økonomi – ikke bruk:** Kontraktsleie ved oppstart, KPI-justert kontraktsleie, Indre vedlikehold, Felleskostnader, Parkeringsleie, Merverdikompensasjon, Vaktmestertjenester, Energi til leieobjektet, Renhold, Kontantinnskudd, Betaling administrativt arbeid, Kostnander, Kost kortleser, m.fl. – alle slike kolonner skal **ikke** brukes som datakilde.

**Sammenligning med Eiendomsportfeb:** Eie1212 har samme type struktur (Lokalisering, Adresse, Matrikkel). Matching kan gjøres på Lokalisering, Adresse og Postnummer, eller Gnr/Bnr, for å knytte Eie1212-rader til Eiendomsportfeb og andre eiendomslister.

**Kjørt mapping (script `finans/map_eie1212_to_portfeb.py`):** Kun eiendomsnøkler (Lokalisering, adresse, Gnr/Bnr) – ingen økonomi. Resultat: **196 Eie1212-rader** har minst én match til Eiendomsportfeb; **195 unike Eiendomsportfeb-eiendommer** mappet; **231 unike (Eie1212, portfeb)-par**. 214 matcher på Lokalisering, 188 på Gnr/Bnr, 211 på adresse (overlap). 53 Eie1212-rader umappet – mange har tom Lokalisering (tomme rader eller ufullstendig data).

### § 20 Eiendomfebruar.csv – kun mapping, ikke økonomidata

**Fil:** `finans/Eiendomfebruar.csv` (ca. 136 000 rader). Transaksjons-/bilagsdata fra økonomisystem (bilag, konto, beløp, periode).

**Viktig:** Bruk **kun** denne filen til å mappe opp enheter/lokasjoner mot eiendommer (Region, Dim1, Dim2 – enhets-ID, enhetsnavn, adresse). **Ikke bruk økonomidata** – kolonnene Beløp, Konto, Innkjøpskategorier, Bilagsnr, Periode m.m. skal **ikke** benyttes som kilde til tall eller analyse.

**Kolonner relevante for eiendomsmapping (bruk kun disse):**

| Kolonne | Bruk til mapping |
|---------|-------------------|
| Region | Geografisk region (Nord, Sør, Øst, Midt). |
| Dim1 | Enhets-ID (f.eks. 635703, 310803). |
| Dim1(T) | Enhetsnavn (f.eks. «Enhet for spesialiserte fosterhjem», «Sundstedtråkka»). |
| Dim2 | Adresse-/lokasjonskode eller ID. |
| Dim2(T) | Adresse/lokasjon (f.eks. «Torget 6, 2000 Lillestrøm», «Ramsrudveien 32, 3518 Hønefoss»). |
| Dim3, Dim4 | Eventuelle ekstra lokasjonsnøkler (valgfritt). |

**Kolonner som er økonomi – ikke bruk:** BA, Bilagsnr, Bilagsdato, År, Periode, Innkjøpskategorier, Innkjøpskategorier(T), Underkategorier, Underkategorier(T), Konto, Konto(T), Beløp, Tekst, Resk.nr, Resk.nr(T), Dim5, Dim6, Dim7, AV – alle disse skal **ikke** brukes som datakilde.

**Sammenligning med Eiendomsportfeb:** Matching kan gjøres på Dim1(T) (enhetsnavn) og særlig Dim2(T) (adresse) mot Eiendomsportfeb-adresser/lokaliseringer. Eventuelt mapping-script skal kun lese mapping-kolonner og rapportere matcher – uten å eksponere eller aggregere Beløp/Konto.

### § 21 Konto – beskrivelser (referanse)

Referansetabell for kontonumre som forekommer i Eiendomfebruar.csv og andre GL-/innkjøpsfiler (Konto / Konto(T)). Brukes til å tolke kostnadstyper; ikke som datakilde til beløp i minnefilens kontekst.

| Konto | Beskrivelse |
|-------|-------------|
| 1268/4960 | Fast bygningsinventar og påkostning, leide bygg - over kr 50 000 |
| 6300 | Leie lokaler andre utleiere |
| 6310 | Leie lokaler fra Statsbygg |
| 6320 | Renovasjon, vann, avløp o.l. |
| 6340 | Strøm og oppvarming |
| 6360 | Renhold lokaler |
| 6364 | Vakthold lokaler |
| 6365 | Vaktmestertjenester |
| 6390 | Annen kostnad lokaler |
| 6391 | Leie parkeringsplass |
| 6395 | Fellesutgifter andre utleiere |
| 6396 | Fellesutgifter (BAD) Bukeravhengige driftsutgifter Statsbygg |
| 6398 | Fellesutgifter Statsbygg - indre vedlikehold |
| 6630 | Reparasjon og vedlikehold leide lokaler |
| 6632 | Oppgradering og påkostning leide lokaler - under kr 50 000 |
| 6662 | Reparasjon og vedlikehold av anlegg, også serviceavtaler |

### § 22 Anleggsnummer – beskrivelser (referanse)

Referansetabell for anleggskontoer (varige driftsmidler, avskrivninger, salg/gevinst/tap). Brukes til å tolke kontonumre i GL/regnskap; ikke som datakilde til beløp i minnefilens kontekst.

| Konto | Beskrivelse |
|-------|-------------|
| 1040 | Programvarelisenser og programvare, kjøpt |
| 1045 | Programvare, egenutviklet |
| 1049 | Akkumulerte avskrivninger lisenser og programvare |
| 1070 | Programvare under utførelse, egenutviklet |
| 1130 | Anlegg under utførelse |
| 1230 | Biler |
| 1239 | Akkumulerte avskrivninger biler |
| 1245 | Andre transportmidler |
| 1249 | Akkumulerte avskrivninger andre transportmidler |
| 1250 | Kontorinventar |
| 1251 | Inventar |
| 1259 | Akkumulerte avskrivninger inventar |
| 1268 | Fast bygningsinventar og påkostning, leide bygg |
| 1269 | Akkumulerte avskrivninger fast bygningsinventar og påkostning, leide bygg |
| 1280 | Datamaskiner og skjermer |
| 1281 | AV-utstyr og nettverkskomponenter |
| 1282 | Annet IKT-utstyr |
| 1289 | Akkumulerte avskrivninger IKT-utstyr |
| 1290 | Andre driftsmidler |
| 1294 | Akkumulerte avskrivninger andre driftsmidler |
| 1297 | Systemkonto anleggsverdiregnskapet, salg |
| 1298 | Systemkonto anleggsverdiregnskapet, ompostering |
| 3800 | Salgssum anleggsmidler |
| 3810 | Gevinst ved avgang av anleggsmidler |
| 4740 | Programvarelisenser |
| 4741 | Kjøp av programvare |
| 4930 | Biler |
| 4940 | Andre transportmidler over kr 50 000 |
| 4950 | Inventar, møbler m.m. over kr 50 000 |
| 4960 | Fast bygningsinventar over kr 50 000 |
| 4980 | IKT utstyr (servere, nettverksutstyr etc) over kr 50 000 |
| 4990 | Andre driftsmidler |
| 4995 | Systemkonto anlegg I |
| 4996 | Systemkonto anlegg II |
| 4997 | Systemkonto anlegg - salg |
| 4998 | Systemkonto anlegg - ompostering |
| 4999 | Interimskonto anlegg |
| 6000 | Avskrivning på lisenser og programvare |
| 6041 | Avskrivning på biler |
| 6042 | Avskrivning på andre transportmidler |
| 6050 | Avskrivning på inventar, andre driftsmidler og lignende |
| 6051 | Avskrivning på IKT-utstyr |
| 6052 | Avskrivning på påkostninger, leid driftsmiddel |
| 6053 | Avskrivning fast bygningsinventar, leide bygg |
| 6070 | Nedskrivning av varige driftsmidler |
| 6071 | Nedskrivning av lisenser og programvare |
| 6551 | Bærbare PCer |
| 7800 | Tap ved avgang av anleggsmidler |

### § 23 Regnskap – beskrivelse av kolonneoverskrifter (dimensjoner)

Beskrivelse av kolonneoverskrifter i regnskapet som ikke er selvforklarende. Gjelder bl.a. Eiendomfebruar.csv og andre GL-eksporter.

| Overskrift | Beskrivelse |
|------------|-------------|
| BA | Bilagsart |
| Dim1 | Koststed |
| Dim1(T) | Koststed (tekst) |
| Dim2 | Prosjektnummer |
| Dim2(T) | Prosjektnummer (tekst) |
| Dim3 | Formål |
| Dim3(T) | Formål (tekst) |
| Dim4 | Finansiering |
| Dim4(T) | Finansiering (tekst) |
| Dim5 | Birknummer |
| Dim5(T) | Birknummer (tekst) |
| Dim6 | Ansattnummer *eller* Anleggsnummer (avhengig av konteringsregel) |
| Dim6(T) | Ansattnummer (tekst) eller Anleggsnummer (tekst) |
| Dim7 | Avtalenummer |
| Dim7(T) | Avtalenummer (tekst) |
| AV | Avgiftstype |

**Merknad:** Konteringsregelen bestemmer om kontoen skal benyttes med ansattnummer eller anleggsnummer i Dim6. Se egen arkfane/regelverk for hvilke kontoer som benytter anleggsnummer i Dim6.

### § 24 Bilagsarter (BA) – forklaring

Forklaring på bilagsarter som forekommer i regnskapet (kolonne BA). Gjelder bl.a. Eiendomfebruar.csv og andre GL-eksporter.

| Bilagsart | Bilagsart (tekst) | Funksjon |
|-----------|-------------------|----------|
| BH | SAP - Hovedlønn | Lønn |
| BR | SAP - Reiser | Reisebilag |
| CA | Håndkasse på flyt | Håndkasser (benyttes ikke lenger) |
| CF | Contempus lev. faktura | Inngående faktura (benyttes ikke lenger) |
| FA | Kundefaktura | Utgående faktura |
| H1 | Hovedbok digitale bilag (AH) | Omposteringsbilag |
| H2 | Hovedbok digitale bilag (AI) | Omposteringsbilag |
| HB | Hovedboksposteringer | Omposteringsbilag |
| IP | Avregning av betalingsoppdrag | Avregning |
| IV | Bokføring inngående faktura | Inngående faktura |
| IW | Bokføring manuelt registrert inngående faktura | Inngående faktura |
| KF | Trigger - Kostnadsfordeling koststed 300200 | Automatisk kostnadsfordeling (ble kun benyttet av region Sør, ser ikke ut til at den benyttes lenger) |
| LE | Leverandørfakturaer | Manuelle leverandørbilag |
| MP | Periodiseringer | Periodisering |
| MT | Anleggstransaksjoner | Anleggstransaksjoner |
| MV | Avsetninger | Avsetninger |
| OP | Omposteringer | Omposteringsbilag (benyttes ikke lenger) |
| RE | Reversering | Reverseringsbilag |

### § 25 Regnskap – dimensjoner, sekkeposter og kontering

**Dimensjoner – «ender som avtalt»:** Forklaringen til de ulike dimensjonene i regnskapet er som avtalt; se vedlegg (jf. § 23 og § 24 i denne minnefilen for oppsummert referanse).

**Sekkeposter – definer på bakgrunn av konto, ikke leverandør:** Anbefaling: definer ulike sekkeposter (aggregeringsnivå / kostnadskategorier) på bakgrunn av **konto**, ikke leverandør. En leverandør kan levere flere utgiftstyper som føres på ulike kontoer i regnskapet.

**Faktura på flere linjer – samme bilagsnummer:** En faktura kan konteres på mange linjer, både etter ulik utgiftstype (f.eks. husleie, felleskostnader og renhold på samme faktura) og fordeles på ulike dimensjoner. Modellen bør være klar over dette og kunne **legge sammen kostnader for inngående fakturaer med samme bilagsnummer**. Dette gjelder bilagsarter som omfatter inngående fakturaer (f.eks. IV, IW, LE). Omposteringsbilag kan i tillegg bestå av mange fakturaer og andre bilagstyper.

**Omposteringsbilag og opprinnelig bilag:** Omposteringsbilag skal (men der syndes det) referere til opprinnelig bilagsnummer. Siden omposteringsbilag ikke berører leverandørreskontro, vil man ikke kunne se hvilken leverandør omposteringen gjelder uten å slå opp opprinnelig bilag. Modellen kan eventuelt tolke tekstfeltet i konteringsstrengen og sjekke bilagsnr som refereres til der, opp mot opprinnelig bilags leverandør.

### § 26 Kjerneproblemet: mapping Dim1 (koststed) ↔ eiendomsadresse

**Utfordringen vi prøver å løse med mappingstabellen:** Mapping mellom avdelinger og eiendom. Ønske om en tabell med to kolonner – **Dim1-kode** og **tilhørende eiendomsadresse** – slik at riktige data kobles til korrekt eiendom.

**Svar fra regnskap – kjerneproblemet:** Koststedsnummer med beskrivelse i ERP (Unit4) er **ikke lik** koststedsnummer med beskrivelse i eiendomssystemet. Det finnes **ingen fellesnevner mellom de to systemene**.

**Eiendomsadresse er ikke en dimensjon i Unit4.** Dim1 har kun koststedsbeskrivelse. Det finnes et register med leveringsadresser (adresser det bestilles varer til), men disse kan **ikke knyttes direkte opp mot Dim1**. Leveringsadresser er likevel lagt ved (én arkfane per region) i tilfelle de kan brukes.

**Integrasjonsprosjektet (avtaleregister i Unit4):** Etablering av avtaleregister i Unit4 der signerte avtaler arkivert i Elements overføres til avtaleregisteret med saksnr og offentlig sakstittel. Fakturaer skal konteres med avtalenr som har generert kostnaden. Formål: bedre oppfølging av forbruk på ulike avtaler. Integrasjonen er straks ferdig.

**Fortsatt ingen direkte kobling:** Heller ikke her er det direkte kobling mellom eiendomsadresse og koststed, fordi avtaler kan arkiveres med ordlyder i sakstittelen som ikke gjenspeiler den nøyaktige eiendomsadressen. På den andre siden vil **kontrakten for eiendommen** ligge arkivert på avtalenummeret som brukes i konteringen – dermed finnes en lenke mellom koststed og kontrakten for eiendommen. Det kan imidlertid ligge mange journalposter på et saksnr, hvorav én kan være kontrakten; det er uklart om KI kan identifisere kontrakten i saksnr for å få sikker adresse.

**Nøyaktighet krever riktig avtalenummer i konteringen.** Det er liten sjanse for at dette blir helt riktig, gitt at mange (med varierende kompetanse) konterer fakturaer. **Eksempel:** Bruk av juridiske tjenester er blitt kontert med avtalenr (saksnr) til en eiendom, selv om det er avtalenummer for avtalen om juridiske tjenester som skal benyttes. Bruk av avtalenummer forveksles ofte med hvordan prosjektnummer skal brukes. I slike tilfeller vil modellen ha lagt juridiske tjenester som kostnader tilhørende eiendomsavtalen, mens de i virkeligheten ikke er reelle eiendomskostnader.

**Modellen bør ta hensyn til konto:** Forhåpentligvis er juridiske tjenester ført på en annen konto enn de som tilhører eiendomskategorien, men det kan også hende at noen feilaktig er kontert på en sekkepostkonto for eiendom. **Usikkerhetsmomenter hele veien.**

**GL → Eiendom: Dim1 = unit_id_erp (i bruk):** Visma Dim1 er koststedskode og tilsvarer **EnhetID** i e-don2/BIRK. Eiendommer som har fått `unit_id_erp` satt ved e-don2-import kan derfor kobles direkte: **GL-import bruker Dim1 → property.unit_id_erp som første match (PASS 0)** før adresse-matching og andre fallbacks. Dette gir en mer pålitelig kobling for alle rader der Dim1 finnes som unit_id_erp på en eiendom.

### § 27 birk_og_plasser.csv – kun mapping (barnevernsinstitusjoner m.m.)

**Fil:** `finans/birk _og_plasser.csv`. I hovedsak barnevernsinstitusjoner og tilhørende plasser; **formål** er gitt i kolonnen Enhetstype (Utledet).

**Viktig:** Bruk **kun** denne filen til eiendoms-/enhetsmapping. **Ikke** bruk kolonner som ikke er nødvendige for mapping (f.eks. antall plasser, budsjett, personer, kontaktinfo).

**Kolonner som brukes til mapping (kun disse):**

| Kolonne | Bruk til mapping |
|---------|-------------------|
| Region | Geografisk region (Nord, Sør, Øst, Vest, Midt). |
| EnhetID | Enhets-ID (BIRK) – kan matche Dim1 i regnskap. |
| Enhetsnavn | Enhetsnavn – match mot Eiendomsportfeb Lokalisering/Avtalenavn. |
| **Enhetskorttype** | **Identifisere avdelinger:** «Avdeling» = avdeling under en institusjon; «Barnevernsinstitusjon» = hele institusjonen. Brukes til å skille avdeling vs institusjon i kostnadsfordeling. |
| Enhetstype (Utledet) | Formål (f.eks. Barnevernsinstitusjon, Institusjonsavdeling). |
| Fylke | Fylke. |
| Kommune | Kommune. |
| Adresse | Gateadresse. |
| Postnummer | Postnummer. |
| Poststed | Poststed. |

**Kolonner som ikke skal brukes til mapping (ikke list opp eller bruk i mapping-script):** Tilhørighet2EnhetID, Tilhørighet2, TilhørighetEnhetID, Tilhørighet, Antall G/K - plasser, Antall budsjetterte plasser, Hjemler, Nedlagt Dato, Eierskapenhet, Lokasjonskode, ePhorte Adm Id, Telefon, Nettside, EPost, Orgnr, Skoleansvarlig, Vara for skoleansvarlig, Helseansvarlig, Vara for helseansvarlig, Familieansvarlig, Vara for Familieansvarlig, Leder – og eventuelle andre kolonner som ikke er nødvendige for å knytte enhet/adresse til eiendom eller for å identifisere avdeling.

**Sammenligning med Eiendomsportfeb:** Matching kan gjøres på Enhetsnavn mot Lokalisering/Avtalenavn, og på Adresse + Postnummer (evt. Poststed) mot Eiendomsportfeb Adresselinje 1 / Adresse og Postnummer. Script: `finans/map_birk_og_plasser_to_portfeb.py` – leser kun mapping-kolonner og rapporterer matcher. **Kjørt mapping:** 477 birk_og_plasser-rader; 151 rader med minst én match til Eiendomsportfeb; 99 unike Eiendomsportfeb-eiendommer matchet; 190 unike (birk_rad, portfeb_lok)-par.

### § 28 Identifisere avdelinger

**Hvor kommer «avdeling» fra?**

| Kilde | Identifikator for avdeling | Merknad |
|-------|----------------------------|--------|
| **birk_og_plasser.csv** (§ 27) | **Enhetskorttype** = «Avdeling» vs «Barnevernsinstitusjon». **Enhetstype (Utledet)** = f.eks. Institusjonsavdeling, Barnevernsinstitusjon, Omsorgssenter. | EnhetID + Enhetsnavn + Enhetskorttype gir enhet og om det er avdeling eller hele institusjonen. |
| **e-don2 / e-dom.txt** (§ 17) | Samme kolonner: **Enhetskorttype** («Avdeling», «Barnevernsinstitusjon»), **Enhetstype (Utledet)**. | Import leser ikke disse i dag – ingen lagring av «skal ha avdeling» (jf. § 3). |
| **Regnskap (Eiendomfebruar, GL)** | **Dim1** = koststed = enhets-ID. **Dim1(T)** = koststedsbeskrivelse. | Unit4 har ikke egen dimensjon for «avdeling»; Dim1 er koststed uten skille avdeling/institusjon. For å knytte Dim1 til avdeling: match Dim1 mot EnhetID i birk_og_plasser/e-don2 og les Enhetskorttype der. |

**Anbefaling (jf. § 3):** Lagre Enhetskorttype (og evt. Enhetstype Utledet) ved import av e-don2/birk_og_plasser, og definer regler for hvilke enheter som skal regnes som «avdeling» i kostnadsfordeling. Ved mapping Dim1 → eiendom: bruk EnhetID fra birk_og_plasser (eller e-don2) som bro – Dim1 = EnhetID – og hent derfra både eiendomsadresse (via mapping mot Eiendomsportfeb) og avdeling (Enhetskorttype = Avdeling).

**Tall fra birk_og_plasser (per uttrekk):** 477 rader – 135 med Enhetskorttype = «Avdeling», 342 med «Barnevernsinstitusjon». Scriptet `map_birk_og_plasser_to_portfeb.py` rapporterer disse tellingene ved kjøring.
