# Lederrapport: Eiendomsdata – Mangler kontrakt og leietaker

**Dato:** 2026-04-11  
**Grunnlag:** Direkte DB-analyse (`audit_properties_full.py` mot `lovely-bravery / BEFS1`)  
**Analysert:** 636 eiendommer i produksjonsdatabasen

---

## Sammendrag

| Kategori | Antall | Andel |
|---|---:|---:|
| Totalt eiendommer i DB | 636 | 100% |
| **Uten aktiv kontrakt** | **451** | **70.9%** |
| Med kontrakt, men uten leietaker (party) | 3 | 0.5% |
| Komplett (kontrakt + leietaker) | 182 | 28.6% |
| Uten avdeling (unit) | 437 | 68.7% |
| Helt tomme poster (ingen data) | 344 | 54.1% |
| Har GL-data men ingen kontrakt | 107 | 16.8% |
| Kontraktleie uten GL-bokføring (avvik) | 21 | 3.3% |

---

## De 451 uten aktiv kontrakt – hva er årsaken?

| Underkategori | Antall | Forklaring |
|---|---:|---|
| Helt tomme poster (ingen data) | 344 (76%) | Eiendomspost eksisterer kun som ID-rad uten avdeling, kontrakt eller regnskapstall |
| Har GL-data men ingen kontrakt | 107 (24%) | Regnskapskobling finnes (koststed/institusjon), men kontrakt er ikke importert |

---

## Regionfordeling

### Uten aktiv kontrakt (451 stk)
| Region | Antall |
|---|---:|
| Øst | 164 |
| Sør | 109 |
| Vest | 77 |
| Midt-Norge | 58 |
| Nord | 42 |
| Bufdir | 1 |

### Med kontrakt men uten leietaker (3 stk – enkelt å fikse)
| Region | Eiendom | Kontrakter | Mangler party |
|---|---|---:|---:|
| Øst | Østfold ungdoms- og familiesenter - avdeling Fossen | 1 | 1 |
| Sør | Thorøya Vaktmesterbolig | 1 | 1 |
| Vest | F3 ungdom - Sjukehusvegen 5 - tillegg (kontor) | 1 | 1 |

---

## Rotårsaker

### 1. Tomme skallposter (338 stk – 53% av alle eiendommer)
Disse postene er opprettet som del av import fra e-don2 eller oversikt-CSV, men har aldri fått avdeling (unit), kontrakt eller regnskapstall koblet til seg. Dette skjer fordi:
- Eiendomsimport (property) og kontraktsimport er **separate prosesser** som aldri ble kjørt for disse
- Match-nøklene mellom CSV-kildene er inkonsistente (`lokalisering_id` vs `gnr/bnr` vs adressetekst)
- Generisk `type=contract`-import **gjør ingen matching mot eksisterende eiendommer** (Cursor-analyse)

### 2. Institusjon med GL men ingen kontrakt (107 stk)
Disse eiendommene er kjent i regnskapet (Agresso koststed-data), men kontrakten er aldri importert. Sannsynlige årsaker:
- Kontrakt finnes som PDF, men er ikke kjørt gjennom `import_bufetat_contracts.py`
- PDF-ekstraksjon feilet (tom adresse, juridisk tekst i adressefelt, postboks-adresse)
- Matching-terskel for adresse for høy → kontrakt havnet som «ikke matchet»

### 3. Tre kontrakter uten leietaker (party_id = NULL)
- `Østfold ungdoms- og familiesenter` – 1 kontrakt uten part
- `Thorøya Vaktmesterbolig` – 1 kontrakt uten part  
- `F3 ungdom – Sjukehusvegen 5` – 1 kontrakt uten part

Disse er enkle å rette – leietakerinfo skal finnes i opprinnelig PDF-kontrakt.

### 4. Kontraktleie uten GL-bokføring (21 stk)
Kontrakt er registrert med et årsbeløp, men regnskapet viser ingen tilsvarende husleiekonto. Kan indikere:
- Kontrakt importert, men fakturering skjer under annen koststed/konto
- Kontrakt avviklet men ikke markert som `terminated`

---

## Tiltaksrekkefølge

### Prioritet 1 – Umiddelbare tiltak (lav innsats, høy effekt)

**1a. Koble leietaker til 3 kontrakter uten party_id**
- Eiendommer: Østfold UFS, Thorøya Vaktmesterbolig, F3 ungdom Sjukehusvegen 5
- Tiltak: Finn leietakerinfo i original kontrakt-PDF → oppdater `contract.party_id` i admin-UI

**1b. Import av kontrakter for 107 eiendommer med GL-data men ingen kontrakt**
- Disse har regnskapskobling – PDF-kontraktene eksisterer sannsynligvis
- Kjør `import_bufetat_contracts.py` med lavere matching-terskel eller manuell matching

### Prioritet 2 – Adressekvalitet (middels innsats)

Av de 39 eiendomsradene i CSV-analysen (PDF-ekstrakt):
- 27 har tom adresse – 15 av disse kan utledes fra filnavnet
- 9 er duplikater (samme PDF gir to rader)
- 5+ har ufullstendig adresse (postboks, juridisk tekst, avklipt tekst)

Se `docs/mangelliste_eiendommer_2026-04-11.csv` for komplett liste med anbefalt handling per rad.

### Prioritet 3 – Skallposter (høy innsats, strukturelt)

338 helt tomme poster krever en beslutning:
- **Alternativ A:** Aktiver avviklet-flagg (`is_discontinued = true`) for eiendommer som ikke lenger er i drift
- **Alternativ B:** Kjør fullstendig re-import med alle kildefiler og konsistent match-nøkkel
- **Alternativ C:** Manuell gjennomgang i grupper per region

---

## Neste steg (konkret)

1. [ ] Fiks 3 kontrakter uten leietaker (party_id) – admin-UI, 30 min
2. [ ] Gjennomgå `docs/mangelliste_eiendommer_2026-04-11.csv` – fyll inn manglende adresser, slett duplikater
3. [ ] Avklar med regionlederne: hvilke av de 338 tomme postene er aktive institusjoner?
4. [ ] Kjør `import_bufetat_contracts.py` for de 107 med GL men ingen kontrakt
5. [ ] Etter import: kjør `audit_properties_full.py` på nytt for å måle fremgang

---

*Rapport generert fra DB-analyse. Kildekode: `backend/scripts/audit_properties_full.py`  
Detaljert mangelliste: `docs/mangelliste_eiendommer_2026-04-11.csv`*
