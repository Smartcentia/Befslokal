# Verifisering: Institusjons-CSV-felter i databasen

**CSV-felter som skal være i databasen:**
Region, Målgruppe, Enhetsnr., Enhetens/Institusjonens navn, Avdelingens koststed, Navn på avdeling, Antall kvalitetssikrede institusjonsplasser avd. pr. 01.01, Antall budsjetterte institusjonsplasser avd. per 01.01

---

## 1. Modeller (SQLAlchemy)

### properties (Property-modell)
| CSV-felt | Kolonne | Status |
|----------|---------|--------|
| Region | `region` | ✅ |
| Målgruppe | `affiliation` | ✅ |
| Enhetsnr. | `lokalisering_id` | ✅ |
| Enhetens/Institusjonens navn | `name` | ✅ |
| Avdelingens koststed | `department_code` | ✅ (tilbakeført) |
| Navn på avdeling | `department_name` | ✅ (tilbakeført) |
| Antall kvalitetssikrede... | `approved_places` | ✅ (aggregerte) |
| Antall budsjetterte... | `budgeted_places` | ✅ (aggregerte) |

### units (Unit-modell)
| CSV-felt | Kolonne | Status |
|----------|---------|--------|
| Avdelingens koststed | `department_code` | ✅ |
| Navn på avdeling | `purpose` | ✅ |
| Målgruppe | `affiliation` | ✅ (per avdeling) |
| Antall kvalitetssikrede... | `approved_places` | ✅ |
| Antall budsjetterte... | `budgeted_places` | ✅ |

---

## 2. Migrasjoner som legger til kolonnene

| Migrasjon | Tabell | Kolonner |
|-----------|--------|----------|
| `20260223_add_missing_property_columns` | properties | lokalisering_id |
| `20260115_183000_phase_1_schema` | properties | region, approved_places (i initial) |
| `20260312_department_code_name` | units | department_code, affiliation, approved_places, budgeted_places |
| `20260312_department_code_name` | properties | DROP department_code, department_name |
| `20260312_rollback_department_properties` | properties | ADD department_code, department_name |
| `20260312_units_zone_uu` | units | zone_type, uu_compliant, uu_notes |

---

## 3. SQL for å verifisere at kolonnene finnes i databasen

Kjør i Supabase SQL Editor:

```sql
-- Sjekk properties
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'properties' 
AND column_name IN ('region', 'affiliation', 'lokalisering_id', 'name', 'department_code', 'department_name', 'approved_places', 'budgeted_places')
ORDER BY column_name;

-- Sjekk units
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'units' 
AND column_name IN ('department_code', 'purpose', 'affiliation', 'approved_places', 'budgeted_places')
ORDER BY column_name;
```

Forventet resultat: alle 8 kolonner for properties, alle 5 for units.

---

## 4. NOT NULL-feil ved import

Hvis import feiler med `null value in column "X" violates not-null constraint`, har databasen NOT NULL på kolonner CSV ikke fyller. Kjør i Supabase SQL Editor:

```sql
ALTER TABLE properties ALTER COLUMN address DROP NOT NULL;
ALTER TABLE properties ALTER COLUMN postal_code DROP NOT NULL;
ALTER TABLE properties ALTER COLUMN city DROP NOT NULL;
```

Import-scriptet bruker fallback-verdier (navn, tom streng) for å unngå noen av disse feilene.

---

## 5. Manglende kolonner – legg til manuelt

Hvis noen kolonner mangler, kjør:

```sql
-- properties
ALTER TABLE properties ADD COLUMN IF NOT EXISTS region VARCHAR;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS affiliation VARCHAR;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS lokalisering_id VARCHAR;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS name VARCHAR;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS department_code VARCHAR;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS department_name VARCHAR;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS approved_places INTEGER;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS budgeted_places INTEGER;

-- units
ALTER TABLE units ADD COLUMN IF NOT EXISTS department_code VARCHAR;
ALTER TABLE units ADD COLUMN IF NOT EXISTS purpose VARCHAR;
ALTER TABLE units ADD COLUMN IF NOT EXISTS affiliation VARCHAR;
ALTER TABLE units ADD COLUMN IF NOT EXISTS approved_places INTEGER;
ALTER TABLE units ADD COLUMN IF NOT EXISTS budgeted_places INTEGER;
```

---

## 6. Import

### Institusjoner (plasser per avdeling)

Script: `backend/scripts/import_institusjoner_csv.py`  
CSV: `backend/data/institusjoner_jan2026.csv`

```bash
cd backend
PYTHONPATH=. railway run python3 -m scripts.import_institusjoner_csv --csv data/institusjoner_jan2026.csv
```

### Oversikt bygg og eiendom (adresser, kontrakter, avdeling–eiendom matching)

Script: `backend/scripts/import_oversikt_bygg_eiendom_csv.py`  
CSV: `backend/data/oversikt_bygg_gk_2026.csv`

Matcher avdelinger mot eiendom via Avtalenavn (institusjonsnavn + «avdeling X»). Oppdaterer properties med adresse, region, usage, plasser; units med plasser og målgruppe.

```bash
cd backend
PYTHONPATH=. railway run python3 -m scripts.import_oversikt_bygg_eiendom_csv --use-db --csv data/oversikt_bygg_gk_2026.csv
```

- `--report` – kun match-rapport, ingen import
- `--create-missing` – opprett nye properties ved manglende match (adresse+navn)

### e-don2/BIRK (hierarkisk enhetsdata)

Script: `backend/scripts/import_edon2_csv.py`  
CSV: Kolonner: Region, Tilhørighet2, TilhørighetEnhetID, Tilhørighet, EnhetID, Enhetsnavn, Enhetskorttype, Enhetstype (Utledet), Antall G/K - plasser, Hjemler, Eierskapenhet, Lokasjonskode, Fylke, Kommune, Adresse, Postnummer, Poststed

Grupperer per Lokasjonskode → én property. Hver rad med EnhetID blir en unit (avdeling).

```bash
cd backend
PYTHONPATH=. railway run python3 -m scripts.import_edon2_csv --csv data/edon2.csv
```

- `--parse-only` – kun parse CSV
- `--dry-run` – ingen endringer lagret
