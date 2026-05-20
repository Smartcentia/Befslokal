# Full beskrivelse: Import Oversikt bygg og eiendom CSV

## 1. Hensikt

Import-scriptet `backend/scripts/import_oversikt_bygg_eiendom_csv.py` importerer data fra **«Oversikt bygg og eiendom - GK og Budsjetterte»** eller **«Eiendomsportefølje- Bufdir»** CSV til BEFS. Regnearkene inneholder kontraktsdata, egnethetsvurderinger, GK-plasser og videreutviklingsplaner for Bufetats eiendommer.

**Hovedmål:**
- Oppdatere eiendommer med Målgruppe, GK-plasser, Hjemmel §, egnethet (1–4) og videreutvikling
- Oppdatere kontrakter med Kontraktsleie, Utleier, Indre vedlikehold, Felleskostnader, Årlig prisjusteringsfaktaktor
- Matche CSV-rader mot eksisterende eiendommer og kontrakter i databasen

---

## 2. To kjøremodus

| Modus | Flagg | Krav | Matching |
|-------|-------|------|----------|
| **Supabase REST API** | (standard) | `SUPABASE_SERVICE_ROLE_KEY` | Kun `lokalisering_id` |
| **Database (Railway)** | `--use-db` | `DATABASE_URL` + `railway run` | Multi-pass (6 strategier) |

### Supabase REST API
- Bruker Supabase REST API direkte
- Krever `SUPABASE_SERVICE_ROLE_KEY` (service_role, ikke anon)
- Matcher **kun** på `lokalisering_id` = kode fra «XXXX - Navn»
- Eiendommer uten matchende `lokalisering_id` hoppes over
- Ingen `--report`-modus

### Database (Railway)
- Bruker `DATABASE_URL` via SQLAlchemy async
- Må kjøres med `railway run` (Railway intern URL er ikke tilgjengelig fra lokal maskin)
- **Multi-pass matching** med 6 strategier (se nedenfor)
- `--report` viser match-rapport uten DB-endringer

---

## 3. Matching-strategier (kun `--use-db`)

| Pass | Strategi | CSV-felt | DB-felt | Beskrivelse |
|------|----------|----------|---------|--------------|
| 1 | `lokalisering_id` | Lokalisering (parse «4711») | `properties.lokalisering_id` | Eksisterende – første prioritet |
| 2 | `navn_contains` | Lokalisering (parse «Furuly» fra «4711 - Furuly») | `properties.name` | Navn inneholder CSV-navn (camelCase-støtte) |
| 3 | `adresse_exact` / `adresse_heuristic` | Adresselinje 1 + Postnr + Poststed | `address`, `postal_code`, `city` | Normalisert adresse (gata→gt, veien→vg) |
| 4 | `adresse_fuzzy` | Adresselinje 1 | `address` | SequenceMatcher ≥ 0.85 |
| 5 | `navn_fuzzy` | Lokalisering-navn | `name` | SequenceMatcher ≥ 0.80 |

**Hjelpefunksjoner:**
- `_parse_lokalisering_navn(lok_raw)` – henter «Furuly» fra «4711 - Furuly»
- `_normalize_address_canonical(addr)` – lowercase, fjern punktum/komma
- `_normalize_address_heuristic(addr)` – gata→gt, veien→vg
- Fuzzy: `difflib.SequenceMatcher` med margin over nest beste (≥ 0.05)

**Ved flere kandidater:** Disambiguering med postnr/poststed.

---

## 4. CSV-format

### Fil
- Standard: `~/Downloads/Oversikt bygg og eiendom - GK og Budsjetterte(Ark1) (2).csv`
- Overstyr med `--csv PATH`

### Separator og encoding
- Støtter **semikolon** (`;`) og **komma** (`,`)
- Prøver: utf-8-sig, utf-8, latin-1, cp1252
- Oversikt bygg: Første rad kan være ekstra header – brukes ikke
- Eiendomsportefølje: Header på rad 1 (første kolonne = «Lokalisering»)

### Datoformat
- `DD.MM.YYYY` (norsk)
- `M/D/YYYY` eller `M/D/YY` (US)

### Eiendomsportefølje-CSV (Ekstra støtte)

Scriptet støtter også **«Eiendomsportefølje- Bufdir»**-formatet. Formatet dekker hele porteføljen (Nord, Midt-Norge, Vest, Sør, Øst, Bufdir) inkl. 6121 og 6125.

**Kolonnenavn-mapping:**
| Eiendomsportefølje | Oversikt bygg | DB |
|--------------------|---------------|-----|
| Kontraktsleie ved oppstart (per år) / KPI-justert kontraktsleie til okt 2025 | Kontraktsleie | `amount.amount_per_year` |
| KPI-justert indre vedlikehold | Indre vedlikehold | `external_data.internal_maintenance_cost` |
| KPI-justert: Felleskostnader | Felleskostnader | `external_data.common_costs` |
| leieregulering | Årlig prisjusteringsfaktaktor | `external_data.regulation_type` |
| adgang til forlengelse og vilkår | – | `external_data.extension_terms` |
| Antall godkjente plasser | Antall G/K - plasser | `approved_places` |

**Flere rader per Lokalisering:** Eiendomsportefølje har ofte hovedkontrakt + tilleggskontrakter. Scriptet prioriterer **hovedkontrakt-rad** (Avtalenavn inneholder «hovedkontrakt» eller «Hovedleiekontrakt»). Fallback: første rad med numerisk Kontraktsleie.

**Beløp-parsing:** Celler med «se hovedkontrakt», «inkludert i hovedkontrakt» etc. returnerer null – raden hoppes over ved kontrakt-match. Ved «4025842 etter reduksjon...» ekstraheres kun første tall.

**Kilde-strategi:** Portefølje-CSV **beriker** eksisterende data – matchende eiendommer/kontrakter oppdateres. Oversikt bygg og Eiendomsportefølje kan brukes uavhengig; ved overlapp overskriver siste import.

### Egnethet (1–4)
| Tall | Farge | Betydning |
|------|-------|-----------|
| 1 | Rød | Lavest egnethet |
| 2 | Oransje | |
| 3 | Gul | |
| 4 | Grønn | Best egnethet |

---

## 5. CSV → Database mapping

### Eiendom (properties)

| CSV-felt | DB-felt | Merknad |
|----------|---------|---------|
| Lokalisering | (matching) | Parse kode + navn |
| Målgruppe | `affiliation` | FVK, BFS, Kontor, Akutt, Omsorg |
| Antall G/K - plasser | `approved_places` | Godkjente plasser |
| Antall budsjetterte plasser | `budgeted_places` | Budsjetterte plasser |
| Hjemmel § | `legal_basis` | Lovparagrafer |
| Egnethet lokalisering | `external_data.egnethet_lokalisering` | 1–4 |
| Egnethet bygg | `external_data.egnethet_bygg` | 1–4 |
| Priortert viderført /utviklet | `external_data.priortert_viderført` | Fri tekst |
| År for videreutvikling | `external_data.år_videreutvikling` | Årstall |
| Kostnader til videreutvikling | `external_data.kostnader_videreutvikling` | Beløp |

### Kontrakt (contracts)

| CSV-felt | DB-felt | Merknad |
|----------|---------|---------|
| Kontraktsleie | `amount.amount_per_year` | Årlig husleie (NOK) |
| Utleier | `party_id` → `parties.name` | Finn/opprett Party |
| Årlig prisjusteringsfaktaktor | `external_data.regulation_type` | F.eks. «100% av KPI på leie» |
| Indre vedlikehold | `external_data.internal_maintenance_cost` | Beløp |
| Felleskostnader | `external_data.common_costs` | Beløp |
| Brukeravhengige driftskostnader | `external_data.user_dependent_costs` | Beløp |
| Avtalenavn | `external_data.contract_name` | Kontraktens navn |

### Kontrakt-matching
- Eiendom har enheter (units); hver enhet har kontrakter
- Match kontrakt på: **Startdato** + **Kontraktsleie** (eller kun Startdato)
- Ved én kontrakt per eiendom: bruk den
- Ved ingen match: raden hoppes over (oppdaterer ikke kontrakt)

---

## 6. Kjøring

### Med Supabase REST API
```bash
cd backend
SUPABASE_SERVICE_ROLE_KEY=<din-nøkkel> python3 scripts/import_oversikt_bygg_eiendom_csv.py [--csv PATH] [--dry-run]
```

### Med Railway (DATABASE_URL)
```bash
cd backend
railway run python3 scripts/import_oversikt_bygg_eiendom_csv.py --use-db [--csv PATH] [--dry-run] [--report]
```

### Flagg
| Flagg | Beskrivelse |
|-------|-------------|
| `--csv PATH` | Full sti til CSV (default: Oversikt bygg). Støtter også Eiendomsportefølje-CSV (f.eks. «Eiendomsportefølje- Bufdir(Sheet1) (3).csv») |
| `--dry-run` | Vis kun hva som ville blitt endret, skriv ikke til DB |
| `--report` | Kun `--use-db`: vis match-rapport uten import |
| `--use-db` | Bruk DATABASE_URL i stedet for Supabase REST |

---

## 7. Rapport-modus (`--report`)

Kun tilgjengelig med `--use-db`. Eksempel på utdata:

```
Rapport: Oversikt bygg CSV vs database
=====================================
Lest 210 rader fra CSV.
Eiendommer i DB: 608
Med lokalisering_id: 45

Treff per metode:
  lokalisering_id:  42
  navn_contains:    12
  adresse_exact:     8
  adresse_heuristic: 2
  adresse_fuzzy:     3
  navn_fuzzy:        2
  ingen:            18

Eksempler uten match:
  [47] 4711 - Furuly | Fridtjof Nansensvei 12, 4514 MANDAL
  ...
```

---

## 8. UI – Finansiell Oversikt

Data importert av scriptet vises i BEFS under **Finansiell Oversikt** på eiendomssiden:

**Kort: «Kontrakts- og egnethetsdata»**
- Kontraktsleie, Utleier, Årlig prisjusteringsfaktaktor
- Målgruppe, Antall G/K-plasser, Antall budsjetterte plasser
- Hjemmel §
- **Egnethet lokalisering** og **Egnethet bygg** – fargekodet (1=rød, 2=oransje, 3=gul, 4=grønn)
- Priortert viderført, År for videreutvikling
- Kostnader til videreutvikling (eller «Kommer» når tom)

---

## 9. Planer og kontekst

### Plan: Flere matching-strategier
- **Problem:** Eiendommer fra e-don2 har `lokalisering_id` = koststed (331810), ikke Oversikt bygg-kode (4711)
- **Løsning:** Multi-pass matching (navn, adresse, fuzzy) – implementert i `--use-db`-modus
- **Risiko:** Fuzzy kan gi feil match – bruk terskel 0.85/0.80 og margin over nest beste

### Plan: CSV Import og Finansiell Oversikt
- **Fase 1:** Import-script (støtte komma, US-dato, egnethet 1–4)
- **Fase 2:** Nytt kort «Kontrakts- og egnethetsdata» under Finansiell Oversikt
- **Fase 3:** API returnerer alle felter
- **Fase 4:** Dokumentasjon

---

## 10. Feilsøking

| Feil | Årsak | Løsning |
|------|-------|---------|
| `Mangler SUPABASE_SERVICE_ROLE_KEY` | Nøkkel ikke satt | Sett i miljø eller `backend/.env` |
| `401 Unauthorized` | Feil eller manglende nøkkel | Bruk `service_role`, ikke `anon` |
| `socket.gaierror` / `nodename not known` | DATABASE_URL peker til Railway intern | Kjør med `railway run` |
| `Fil ikke funnet` | CSV finnes ikke på default-sti | Bruk `--csv` med full sti |
| `Rader uten matchende eiendom` | Ingen match for lokalisering | Bruk `--use-db --report` for å se hva som mangler |

---

## 11. Relaterte filer

- **Script:** `backend/scripts/import_oversikt_bygg_eiendom_csv.py`
- **Dokumentasjon:** `docs/OVERSIKT_BYGG_EIENDOM_CSV.md`
- **Plan matching:** `.cursor/plans/flere_matching-strategier_import_dc7fd0a8.plan.md`
- **Plan CSV/UI:** `.cursor/plans/csv_finansiell_oversikt_import_796eda3c.plan.md`
- **UI:** `frontend/app/properties/[id]/page.tsx` (Finansiell Oversikt)
