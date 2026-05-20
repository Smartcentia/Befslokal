# Plassering av Avdeling mot Eiendom

## Bakgrunn og Formål
Tradisjonelt har det vært et gap mellom eiendomsforvaltningen (fysiske bygg) og regnskapsavdelingen (finansielle poster i Unit4). Regnskapet opererer med avdelingskoder (**Dimensjon 1**), mens eiendomsregisteret opererer med adresser og lokasjonskoder. Uten en teknisk bro mellom disse to verdenene, må kostnadsallokering og analyser ofte gjøres manuelt.

Formålet med denne integrasjonen er å:
1.  **Automatisere kostnadsovervåking**: Ved å knytte Avdelings-ID (Dim 1) direkte til Eiendoms-ID (`unit_id_erp`), kan systemet automatisk aggregere kostnader per fysisk bygg.
2.  **Øke datakvalitet**: Sikre at fakturaer bokføres på korrekte enheter og gi automatiske varsler dersom kostnader føres på bygg som er merket som "Nedlagt" i BEFS.
3.  **Muliggjøre avansert analyse**: Ved å ha både regnskapsdata og operasjonelle data (f.eks. antall budsjettplasser fra `e-don2.txt`) i samme system, kan vi beregne KPI-er som *"Driftskostnad per plass"* i sanntid.

Dette dokumentet forklarer hvordan systemet nå kobler regnskapsdata fra ERP (Unit4) direkte mot de fysiske eiendommene i BEFS. Nøkkelen til denne koblingen er integrasjonen av `EnhetID` inn i eiendomsmodellen.

## Hvordan det fungerer
Regnskapssystemet bruker **Dimensjon 1 (Enhet/Avdeling)** for å bokføre alle kostnader. Tidligere var disse "avdelingene" bare numre i regnskapet uten en direkte, teknisk kobling til eiendomsregisteret. 

Ved å legge til feltet `unit_id_erp` på hver eiendom, kan vi nå lese en regnskapsfil og automatisk si: *"Denne fakturaen tilhører avdeling 12345, og avdeling 12345 er identisk med Storgata 1"*.

---

## 5 Eksempler på praktisk bruk

### 1. Vedlikeholdsfaktura fra Unit4
En rørlegger sender en faktura på 15 000 kr. I Unit4 er denne bokført på `Konto 6600` (Vedlikehold) og `Enhet 40220`.
- **Systemet leser**: Regnskapslinje med `Enhet 40220`.
- **Systemet søker**: Ser i eiendomsregisteret etter `unit_id_erp = '40220'`.
- **Resultat**: Beløpet legges automatisk til i kostnadsoversikten for "Oslo Barne- og ungdomssenter".

### 2. Strømregning (ELex / Energioppfølging)
Strømkostnader kommer ofte som samlefiler. Hver måler er koblet til et bygg eller en avdeling.
- **Systemet leser**: Importfil med `Lokasjonskode 14.22.41`.
- **Systemet søker**: Bruker den nye matching-logikken som ser på både `lokalisering_id` og `unit_id_erp`.
- **Resultat**: Strømkostnaden plasseres riktig selv om avdelingsnavnet i strømfilen er litt annerledes enn i BEFS.

### 3. Budsjettoppfølging per Plass
Du har nå `Antall budsjetterte plasser` fra e-don2.
- **Systemet leser**: Faktiske lønnskostnader for en institusjon fra regnskapet (via `unit_id_erp`).
- **Beregning**: (Sykepleierlønn + Mat + Strøm) / `budgeted_places`.
- **Resultat**: Du får ut nøyaktig "Kostnad per plass" automatisk på dashbordet.

### 4. Husleieinntekter og Felleskostnader
Hvis en leietaker betaler leie, bokføres dette ofte på eiendommens egen "inntektsavdeling".
- **Systemet leser**: Kreditpostering i regnskapsfilen på `Enhet 50300`.
- **Systemet kobler**: Ser at `unit_id_erp` for "Hovedkontoret" er `50300`.
- **Resultat**: Kontraktens dekningsgrad oppdateres i sanntid på eiendomssiden.

### 5. Avstemming av Nedlagte Bygg
E-don2 inneholder `Nedlagt Dato`.
- **Systemet leser**: Regnskapsposteringer som tikker inn i februar 2026.
- **Sjekk**: Ser at eiendommen er merket som "Nedlagt" fra 01.01.2026 i BEFS.
- **Resultat**: Systemet gir et varsel i dashbordet: *"Kostnader registrert på avviklet enhet (Dim 1)"*. Dette hjelper regnskapsavdelingen å rydde opp i gamle avdelingsstrukturer.
