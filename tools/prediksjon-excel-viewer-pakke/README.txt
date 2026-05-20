================================================================================
BEFS / KNOWME — Prediksjon Excel, lokal drill-down (pakke til sluttbruker)
================================================================================
Versjon: 1.4 (april 2026)
Innhold: index.html + vendor/xlsx.full.min.js + prediksjon_2027_export.xlsx (DEMO)

VIKTIG — HVA «70 %» OG «50 %» ER (OG IKKE ER)
---------------------------------------------
I Excel-oversikten betyr «Scenario xgb70 (XGB-gulv 70 %)» og «…50 %» to ulike
modellscenarier for hvor streng den NEDRE GRENSEN (gulvet) fra XGBoost skal
være i forhold til maskinlæringsprediksjon på tvers av porteføljen, etter at
Holt-Winters er kjørt.

Det er IKKE:
  • «70 % eller 50 % internt forbruk» eller aktivitetsnivå
  • Holt-Winters α eller β (de er fortsatt f.eks. α=0,7 β=0,3 i drift)

GL 2025 (faktisk) og prediksjon 2027 er heller ikke samme definisjon — sammenlign
bevisst. Eiendommer uten prediksjon påvirker totaler og Excel-rader ulikt; se
arket «Forklaring» i eksport fra BEFS.

MEDFOLGENDE EXCEL (DEMO)
------------------------
Filen prediksjon_2027_export.xlsx i denne mappen er generert med syntetiske tall
kun for at viewer og struktur kan testes uten BEFS-tilkobling.

For EKTE prediksjonstall (samme som API):
  • Fra BEFS: last ned eksport fra prediksjon-siden, eller
  • Fra utviklermaskin med DATABASE_URL:
      cd backend
      python scripts/export_prediksjon_2027_xlsx.py -o <sti>/prediksjon_2027_export.xlsx

Opprett DEMO-fil pa nytt (syntetiske tall):
      cd backend
      python scripts/generate_prediksjon_2027_demo_xlsx.py

HVOR KOMMER holt_winters_2027_xgb70 / xgb50 FRA? (for IT / økonomi)
---------------------------------------------------------------------
Prediksjon lagres i databasen i tabellen budget med:
  year = 2027, is_synthetic = true,
  data_source = holt_winters_2027_xgb70  eller  holt_winters_2027_xgb50

Begge suffiksene fylles av samme motor:
  backend/app/services/prediction_service.py  (BudgetPredictionService.predict_all_properties)

Operativ kjøring uten HTTP (anbefalt i produksjon / Railway):
      cd backend
      python scripts/run_prediction.py
  → skriver holt_winters_2027_xgb70 (standard).

For holt_winters_2027_xgb50: samme script, annet suffiks:
      cd backend
      PREDICTION_DATA_SOURCE_TAG=xgb50 python scripts/run_prediction.py

Excel-eksporten (API og export_prediksjon_2027_xlsx.py) leser begge scenarioene fra budget.
Hvis bare xgb70 er kjørt, vil XGB Gulv 50 %-kolonner være tomme / null — kjør da scriptet
også med PREDICTION_DATA_SOURCE_TAG=xgb50 (evt. etter å ha justert parametre i scriptet
dersom 50 %-scenariet skal ha andre Holt-Winters-innstillinger enn 70 %).

HVA DETTE ER
------------
En enkel nettside som åpnes i nettleseren. Du laster inn en Excel-fil eksportert
fra BEFS (prediksjon 2027 med arkene Eiendom_kategori, GL_konto, GL_bilag).
Ingenting lastes opp til internett — alt skjer på din PC.

KRAV
----
• Windows, macOS eller Linux med en moderne nettleser (Chrome, Edge, Firefox,
  Safari).
• Hele mappen må ligge slik den er: index.html og undermappen vendor/ skal
  ikke flyttes fra hverandre og vendor/ skal ikke slettes.

ZIP-FIL (leveranse til bruker)
------------------------------
Bygges med:  bash tools/prediksjon-excel-viewer-pakke/LAG_ZIP_TIL_BRUKER.sh
Standard filnavn:  tools/BEFS-Prediksjon2027-Excel.zip (hele mappen prediksjon-excel-viewer-pakke arkiveres).

SLIK STARTER DU
---------------
1. Pakk ut ZIP-filen til en valgfri mappe (f.eks. Skrivebord).
2. Dobbeltklikk på index.html, ELLER høyreklikk → Åpne med → nettleser.

SLIK BRUKER DU DET
------------------
1. Enten: bruk den medfolgende DEMO-filen prediksjon_2027_export.xlsx (test),
   eller: logg inn i BEFS, ga til prediksjon, og last ned nyeste Excel-eksport.
2. I denne appen: klikk «Velg fil» og velg .xlsx-filen.
3. Rapport-hub (øverst etter innlesing): velg region, deretter «hele porteføljen»
   (alle eiendommer i filteret) ELLER én eiendom — via nedtrekksliste eller
   søk + hurtigknapper. Punkt 3–5 lenger ned oppdateres automatisk for valgt omfang.
4. «Bygg rapport» lager et statisk sammendrag (utskrift / .html) for samme omfang,
   pluss historikk og kostnadsgrunnlag der disse arkene finnes i Excel-filen.
5. Drill-down: velg kategori → konto → bilagslinjer (hvis arket finnes i filen).

MERKNAD OM BILAG
----------------
Eksporten kan inneholde et begrenset antall bilagslinjer (for filstørrelse).
Full detalj finnes i BEFS / regnskapssystem.

TEKNISK (for IT)
----------------
• Tredjepartsbibliotek: SheetJS (xlsx) Community Edition — se vendor/LICENSE.txt
• Ingen installasjon, ingen server, ingen nettforbindelse nødvendig etter at
  pakken er komplett (vendor inkludert).

FEIL: «Excel-bibliotek mangler» / XLSX
--------------------------------------
Årsak nesten alltid: bare index.html er kopiert, eller vendor/ mangler etter utpakking.

Riktig struktur etter utpakking:
  prediksjon-excel-viewer-pakke/
    index.html
    README.txt
    vendor/
      xlsx.full.min.js
      LICENSE.txt

Siden prøver automatisk reservebibliotek fra internett hvis vendor/ mangler (krever nett).
Alternativ: i mappen, kjør  python3 -m http.server  og åpne http://localhost:8000/

SUPPORT
-------
Spørsmål om innhold i Excel-filen: eier av BEFS-miljøet.
Feil «Fant ikke arket Eiendom_kategori»: bruk nyeste eksport fra BEFS.

================================================================================
