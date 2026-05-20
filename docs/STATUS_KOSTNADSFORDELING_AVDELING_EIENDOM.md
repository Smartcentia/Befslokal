# Status: Kostnadsfordeling per eiendom og avdeling

**Dato:** 3. februar 2026  
**Formål:** Sjekke om korrelasjon eiendom ↔ avdeling og identifikasjon av avdelinger (Birk/e-don2) er på plass.

---

## 1. Mål og bakgrunn

- **Mål:** Kunne fordele kostnader per eiendom og tilhørende avdeling.
- **Utfordring:** Det finnes ikke en ferdig dimensjon i regnskapet som entydig korrelerer eiendom med riktig avdeling.
- **Tilnærming:** Konvertering/korrelasjonstabell som bruker tilgjengelige data (adresse, navn, koder) for å knytte eiendom til avdeling.

---

## 2. Korrelasjonstabell (master_data_crosswalk)

### 2.1 Hva som finnes

| Element | Status |
|--------|--------|
| **DB-tabell** | `master_data_crosswalk` er opprettet (migrasjon `8be2957122b1_add_master_data_crosswalk.py`) |
| **Modell** | `MasterDataCrosswalk` i `backend/app/models/master_data_crosswalk.py` – felt: relation_type, source_type, source_id, target_type, target_id, status, collision_flag, match_method, score, confidence, run_id, valid_from/to, audit_metadata |
| **Script som bygger koblinger** | `backend/scripts/reconcile_master_data.py` – lager BIRK → PROPERTY (LOCATED_AT) basert på adresse + navn (normalisert, fuzzy) |

### 2.2 Hva som mangler

| Element | Status |
|--------|--------|
| **Skriving til DB** | `reconcile_master_data.py` skriver kun til CSV (master_crosswalk_audit.csv, approval_queue_pending.csv, birk_clean.csv, property_master.csv). Den **fyller ikke** tabellen `master_data_crosswalk` i databasen. |
| **Bruk ved GL-import** | I `data_management.py` (import av GL-transaksjoner) brukes **ikke** `master_data_crosswalk`. Property-matching bruker: (1) learned_mappings (avd.kode → property_id), (2) dim2_name/adresse mot eiendomsliste, (3) rebooking H1/H2/HB, (4) dim1_fallback og department_name. Altså er korrelasjonstabellen ikke integrert i kostnadsfordelingen. |
| **Dim1 → PROPERTY** | Reconcile-scriptet lager kun **BIRK → PROPERTY**. ERP_INGEST_SPEC beskriver FUNDS (Dim1 ↔ BIRK) og BOOKED_ON (Dim1 ↔ PROPERTY), men det finnes ingen kode som leser fra crosswalk for å mappe Dim1 til property_id ved import. |

**Konklusjon:** Korrelasjonstabellen er modellert og det finnes et script som bygger BIRK→PROPERTY-koblinger, men disse skrives ikke til DB og brukes ikke ved GL-import. For å fordele kostnader per eiendom/avdeling må enten (a) crosswalk fylles i DB og GL-import leser derfra, eller (b) eiendommer får pålitelig `lokalisering_id`/`unit_id_erp` som matcher regnskapets Dim1, og import bruker det eksplisitt.

---

## 3. Eiendom ↔ avdeling i dag

- **properties:** Har `lokalisering_id` og `unit_id_erp` (EnhetID fra e-don2). Regnregler sier at Dim 1 (koststed) skal kunne bindes til `properties.lokalisering_id`.
- **GL-import:** Bruker `department_code` og `department_name` (Dim1) og matcher mot eiendom via adresse/navn og “learned” mapping – ikke via `master_data_crosswalk` eller direkte `unit_id_erp`/`lokalisering_id`-oppslag på properties.
- **e-don2-import:** Setter `unit_id_erp` og `lokalisering_id` på eiendommer. Da kan GL i teorien bruke Dim1 = EnhetID for å finne property – men i nåværende GL-import brukes ikke property.unit_id_erp eller property.lokalisering_id som første prioritet.

---

## 4. Birk – avdelinger vs ikke-avdelinger

### 4.1 Kilder

- **Birk** (i reconcile): `birk_raw.csv` med kolonner som EnhetID, Navn, Adresse, Postnr. Brukes til BIRK → PROPERTY (adresse/navn). Ingen kolonne for type (avdeling vs hele institusjonen).
- **e-don2** (backend/e-don2.txt): Har kolonnene **Enhetskorttype** (f.eks. "Avdeling", "Barnevernsinstitusjon") og **Enhetstype (Utledet)** (f.eks. "Barnevernsinstitusjon", "Institusjonsavdeling", "Omsorgssenter"). Dette er nødvendig for å skille “avdeling” (fysisk enhet på eiendom) fra “hele barnevernsinstitusjonen” (som kan være admin eller overordnet enhet).

### 4.2 Hva som er implementert

| Sted | Bruk av Enhetskorttype / Enhetstype |
|------|-------------------------------------|
| **e-don2-import** (`data_management.import_edon2_csv`) | Leser **ikke** Enhetskorttype eller Enhetstype – de lagres ikke på Property eller i external_data. |
| **Property-modell** | Har ikke felt som `unit_type`, `is_avdeling` eller tilsvarende. |
| **reconcile_master_data (Birk)** | Bruker bare BIRK-enheter uten å skille avdeling vs institusjon; alle BIRK-rader behandles likt. |

**Konklusjon:** Vi identifiserer ikke i koden hvilke enheter som skal regnes som avdelinger (og f.eks. skal få kostnader fordelt på eiendom) og hvilke som ikke skal det. Informasjonen finnes i e-don2 (Enhetskorttype / Enhetstype), men brukes ikke.

---

## 5. Anbefalte tiltak

### 5.1 Korrelasjonstabell (kostnad eiendom ↔ avdeling)

1. **Fylle crosswalk i DB:** Utvide `reconcile_master_data.py` (eller eget script) slik at godkjente/kvalitetssikrede koblinger skrives til `master_data_crosswalk` (INSERT/UPDATE) i stedet for kun CSV.
2. **Bruk ved GL-import:** I `data_management.py` (GL-import):
   - Legge inn et pass som slår opp Dim1 (department_code) i `master_data_crosswalk` (f.eks. source_type=DIM1, source_id=department_code → target_type=PROPERTY, target_id=property_id), og setter `property_id` på transaksjonen når det finnes treff.
   - Alternativt/ supplerende: bruke `property.unit_id_erp` / `property.lokalisering_id` når Dim1 matcher (eksakt eller normalisert), slik at kostnader kan fordeles per eiendom.
3. **Dim1 i crosswalk:** Hvis regnskapet bruker Dim1 (avdelingskode) og ikke BIRK EnhetID direkte, må crosswalk enten inneholde DIM1 → PROPERTY eller DIM1 → BIRK → PROPERTY, og GL-import må bruke det.

### 5.2 Birk / e-don2 – avdeling vs ikke-avdeling

1. **Lagre type i e-don2-import:** I `import_edon2_csv`, lese kolonnene **Enhetskorttype** og **Enhetstype (Utledet)** og lagre dem på eiendommen, f.eks. i `external_data` (som `edon2_enhetskorttype`, `edon2_enhetstype`) eller på nye kolonner på Property (f.eks. `unit_type` / `is_avdeling`).
2. **Regler for “skal ha avdeling”:** Dokumentere (og evt. implementere) regler for hvem som skal behandles som avdeling i kostnadsfordeling (f.eks. Enhetskorttype = "Avdeling" eller Enhetstype = "Barnevernsinstitusjon" / "Institusjonsavdeling" – avhengig av forretningsregler).
3. **Birk (birk_raw.csv):** Hvis Birk-eksporten har type-informasjon, inkluder den i reconcile og bruk den i crosswalk (f.eks. kun koble kostnader til BIRK-enheter som er avdelinger). Hvis ikke, vurdere å bruke e-don2 som kilde til “avdeling ja/nei” for samme EnhetID.

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
| e-don2 kolonner | `backend/e-don2.txt` (header: Enhetskorttype, Enhetstype (Utledet)) |
