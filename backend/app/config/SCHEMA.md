# Database Schema for Text-to-SQL

Her er oversikten over databasen du kan spørre mot.
Databasen er PostgreSQL.

## Viktige regler for ruting til tabeller

- **Budsjett-spørsmål:** Bruk ALLTID tabellen `budget`. Ikke prøv å beregne budsjett fra `contracts`.
- **Regnskap/Faktiske kostnader:** Bruk ALLTID tabellen `gl_transactions`.
- **Økonomiske Avvik (Variance):** Hvis brukeren spør om *økonomisk* avvik eller budsjettavvik, beregn som `budget.amount - gl_transactions.amount` gruppert på kategori/eiendom/periode.
- **Driftsavvik / HMS-avvik / Saker:** Hvis brukeren spør om avvik i betydningen feil, mangler, HMS-avvik eller åpne saker, bruk tabellen `internal_control_cases`. Dette er den primære kilden for operasjonelle avvik.
- **Risiko:** Bruk `risk_assessments` and `risk_factors`.

## Tabeller

### 1. `properties` (Eiendommer)

- `property_id` (UUID): Unik ID.
- `name` (String): Navnet på eiendommen (f.eks. "Storgata 10").
- `address` (String): Gateadresse.
- `city` (String): By/sted.
- `postal_code` (String): Postnummer.
- `region` (String): Region (f.eks. "Region Øst").
- `latitude` (Float, nullable): Breddegrad (WGS84). For geografiske spørsmål («lengst nord», «nordligst»): i Norge er **lengst nord** den eiendommen med **høyeste** `latitude`. Bruk `WHERE latitude IS NOT NULL` og sorter f.eks. `ORDER BY latitude DESC NULLS LAST`.
- `longitude` (Float, nullable): Lengdegrad (WGS84).
- `total_area` (Float): Totalt areal i m2 (direkte felt, ikke JSONB).
- `land_area` (Float): Tomteareal i m2.
- `construction_year` (Integer): Byggeår.
- `energy_label` (String): Energimerking (f.eks. "B").
- `malgruppe` (String, nullable): Målgruppe (f.eks. "FVK", "BFS", "Omsorg").
- `contract_rent_nok` (Numeric 14,2, nullable): Avtalefestet husleie fra leieavtale/CSV (~181 eiendommer, ~319 MNOK). **Ikke det samme som gl_rent_2025** – overskrives aldri av GL-data.
- `contract_maint_nok` (Numeric 14,2, nullable): Indre vedlikehold fra kontrakt.
- `contract_common_nok` (Numeric 14,2, nullable): Felleskostnader fra kontrakt.
- `contract_user_ops_nok` (Numeric 14,2, nullable): Brukeravhengige driftskostnader fra kontrakt.
- `extension_terms` (String, nullable): Adgang til forlengelse og vilkår.
- `price_adj_clause` (String, nullable): Prisjusteringsklausul / KPI-regulering.
- `gl_rent_2025` (Numeric 14,2, nullable): Faktisk husleie 2025 fra GL-regnskap (srs_kategori='Lokaler'), ~145 eiendommer, ~430 MNOK. **Ikke det samme som contract_rent_nok** – overskrives aldri av kontraktsdata.
- `lok_omrade` (String 50, nullable): Lok: Område fra Eiendomsportefølje-CSV (f.eks. "03 - Trøndelag").
- `lok_distrikt` (String 50, nullable): Lok: Distrikt fra Eiendomsportefølje-CSV (f.eks. "01 - Nord").
- `fylke` (String 50, nullable): Fylke.
- `leased_area_kvm` (Numeric 10,1, nullable): Areal inkl. fellesareal i leiekontrakt (kvm), ~181 eiendommer.
- `elements_id` (String 200, nullable): Elements saksnummer, ~207 eiendommer.
- `utleier_kategori` (SmallInt, nullable): Utleier-kategori: 1 = privat, 2 = offentlig, ~213 eiendommer.
- `egnethet_lokalisering` (String 100, nullable): Eiendomsegnethet – lokalisering (f.eks. "4 – Grønn").
- `egnethet_bygg` (String 100, nullable): Eiendomsegnethet – bygg.
- `prioritert_videroforing` (String 50, nullable): Prioritert viderføring/utvikling.
- `ar_videreutvikling` (Integer, nullable): År for videreutvikling.
- `kostnader_videreutvikling` (Numeric 14,2, nullable): Estimerte kostnader til videreutvikling.
- `external_data` (JSONB): Tilleggsdata (valgfritt).
  - **Vedlikeholdskostnad / kostnad per kvm:** `external_data->'financials'->>'total_manual_expenses'` (float) og `external_data->'financials'->>'total_spend_csv'` (float). Summen er totalkostnad vedlikehold. Kostnad per kvm = totalkostnad / total_area (når total_area > 0).

> **KRITISK – to separate husleie-kilder:** `contract_rent_nok` er avtalefestet leie fra leieavtale; `gl_rent_2025` er bokført husleie fra GL-regnskap 2025. Disse representerer ulike sannheter og må aldri overskrives av hverandre. Bruk `contract_rent_nok` for budsjett/kontraktsanalyse, og `gl_rent_2025` for regnskapsanalyse og avvik.

### 2. `units` (Utleieobjekter/Enheter)

Kobling mellom eiendom og kontrakt.

- `unit_id` (UUID): Unik ID.
- `property_id` (UUID): Fremmednøkkel til `properties`.
- `external_data` (JSONB):
  - `area` (Number): Areal på enheten i m2.
  - `usage_type` (String): Type bruk (Kontor, Bolig, etc.).

### 3. `contracts` (Leiekontrakter)

- `contract_id` (UUID): Unik ID.
- `unit_id` (UUID): Fremmednøkkel til `units`.
- `party_id` (UUID): Fremmednøkkel til `parties` (Huseier/Motpart).
- `status` (String/enum): Status på kontrakt. **VIKTIG: Bruk lowercase** – `'active'` (aktiv), `'terminated'` (avsluttet). Ikke 'Aktiv'.
- `start_date` (Date/String): Startdato (YYYY-MM-DD).
- `end_date` (Date/String): Sluttdato (YYYY-MM-DD). NB: Kan være NULL for løpende.
- `amount` (JSONB): Økonomiske data.
  - `amount_per_year` (Number): Årlig leie (NOK).
  - `amount_per_month` (Number): Månedlig leie.
- `filename_number` (String): Kontraktnummer.

### 4. `parties` (Parter/Huseiere)

- `party_id` (UUID): Unik ID.
- `name` (String): Navn på selskap/person.
- `orgnr` (String): Organisasjonsnummer.
- `role` (String): Rolle (f.eks. "Landlord", "Tenant").

### 5. `budget` (Budsjett)

- `budget_id` (UUID): Unik ID.
- `property_id` (UUID): Fremmednøkkel til properties.
- `year` (Integer): Budsjettår.
- `month` (Integer): Budsjettmåned (1-12).
- `category` (String): Kostnadskategori (f.eks. "Vedlikehold", "Energi", "Renhold").
- `amount` (Float): Budsjettert beløp.

### 6. `gl_transactions` (Regnskapsposter/Faktiske kostnader)

- `transaction_id` (UUID): Unik ID.
- `property_id` (UUID): Fremmednøkkel til properties.
- `transaction_date` (Date): Dato for transaksjonen.
- `year` (Integer): Regnskapsår.
- `month` (Integer): Regnskapsmåned.
- `amount` (Float): Beløp (negativt for kostnad, positivt for inntekt).
- `category` (String): Kostnadskategori.
- `description` (String): Beskrivelse fra regnskapet.
- `account_code` (String): Hovedbokskonto (f.eks. 3000=Leieinntekt, 6000=Strøm, 6100=Parkering).
- `vendor` (String): Leverandør/Kreditor.

### 7. `internal_control_cases` (Driftsavvik / Saker)

Primær tabell for HMS-avvik, feil og mangler.

- `case_id` (UUID): Unik ID.
- `property_id` (UUID): Fremmednøkkel til `properties`.
- `assigned_user_id` (UUID): Hvem som eier saken (F.K. til `users`).
- `title` (String): Kort beskrivelse av avviket.
- `description` (String): Detaljert beskrivelse.
- `status` (String): 'open', 'closed', 'in_progress'.
- `priority` (String): 'low', 'medium', 'high', 'critical'.
- `case_type` (String): 'monthly', 'quarterly', 'annual'.
- `due_date` (DateTime): Frist.
- `completed_at` (DateTime): Når saken ble lukket.

### 8. `risk_assessments` (Risikovurderinger)

- `assessment_id` (UUID): Unik ID.
- `property_id` (UUID): Fremmednøkkel til `properties`.
- `overall_risk_score` (Float): Samlet score (0-100).
- `risk_category` (String): 'LOW', 'MEDIUM', 'HIGH'.
- `assessment_date` (Date): Når vurderingen ble gjort.

### 9. `scheduled_activities` (Planlagte HMS-aktiviteter)

- `activity_id` (UUID): Unik ID.
- `property_id` (UUID): Fremmednøkkel til `properties`.
- `title` (String): Navn på aktivitet (f.eks. "Eksitasjonsprøve brann").
- `category` (String): 'brann', 'teknisk', 'hms', 'sikkerhet'.
- `next_due_date` (DateTime): Neste frist.
- `enabled` (Boolean): Om aktiviteten er aktiv.

## JSONB-syntaks i PostgreSQL

### Grunnleggende operasjoner

**Hente verdier fra JSONB:**

- Tekstverdi: `field->>'key'` (returnerer TEXT)
- Objekt/array: `field->'key'` (returnerer JSONB)
- Nested: `field->'parent'->>'child'`
- Array-element: `field->0->>'key'` (første element)

**Type-casting (MÅ gjøres for sammenligning/agregering):**

- Til tall: `(field->>'amount')::numeric` eller `(field->>'amount')::float`
- Til dato: `(field->>'date')::date`
- Til boolean: `(field->>'active')::boolean`

### Eksempler på JSONB-felter i databasen

**contracts.amount (JSONB):**

```json
{
  "amount_per_year": 1200000,
  "amount_per_month": 100000,
  "currency": "NOK"
}
```

**units.external_data (JSONB):**

```json
{
  "area": 150.5,
  "usage_type": "Kontor",
  "master_data": {
    "area": 150.5,
    "rooms": 5
  }
}
```

**properties.external_data (JSONB):**

```json
{
  "financials": {
    "total_manual_expenses": 50000,
    "transactions_2025": [
      {"date": "2025-01-15", "amount": 10000, "account": "6600"},
      {"date": "2025-02-20", "amount": 15000, "account": "6600"}
    ]
  }
}
```

## Eksempler på SQL

### Grunnleggende spørringer

**Finne total årlig leie:**

```sql
SELECT SUM((amount->>'amount_per_year')::numeric) as total_rent
FROM contracts 
WHERE status = 'active'
  AND amount->>'amount_per_year' IS NOT NULL
```

**Finne gjennomsnittlig månedlig leie:**

```sql
SELECT AVG((amount->>'amount_per_month')::numeric) as avg_monthly_rent
FROM contracts
WHERE status = 'active'
  AND amount->>'amount_per_month' IS NOT NULL
```

**Finne kontrakter som utløper i 2026:**

```sql
SELECT c.filename_number, p.name, c.end_date 
FROM contracts c
JOIN units u ON c.unit_id = u.unit_id
JOIN properties p ON u.property_id = p.property_id
WHERE c.end_date >= '2026-01-01' 
  AND c.end_date <= '2026-12-31'
ORDER BY c.end_date
```

### Avanserte JSONB-spørringer

**Topp 5 dyreste eiendommer (med JSONB-agregering):**

```sql
SELECT 
    p.name, 
    p.address,
    SUM((c.amount->>'amount_per_year')::numeric) as total_rent
FROM contracts c
JOIN units u ON c.unit_id = u.unit_id
JOIN properties p ON u.property_id = p.property_id
WHERE c.status = 'active'
  AND c.amount->>'amount_per_year' IS NOT NULL
GROUP BY p.property_id, p.name, p.address
ORDER BY total_rent DESC
LIMIT 5
```

**Finn enheter med areal fra JSONB:**

```sql
SELECT 
    u.unit_id,
    p.name as property_name,
    (u.external_data->>'area')::float as area_m2,
    u.external_data->>'usage_type' as usage_type
FROM units u
JOIN properties p ON u.property_id = p.property_id
WHERE u.external_data->>'area' IS NOT NULL
ORDER BY (u.external_data->>'area')::float DESC
```

**Finn eiendommer med høyest kostnad fra external_data:**

```sql
SELECT 
    name,
    address,
    (external_data->'financials'->>'total_manual_expenses')::numeric as total_expenses
FROM properties
WHERE external_data->'financials'->>'total_manual_expenses' IS NOT NULL
ORDER BY (external_data->'financials'->>'total_manual_expenses')::numeric DESC
LIMIT 10
```

**Iterere over JSONB-array (transaksjoner):**

```sql
SELECT 
    p.name,
    t->>'date' as transaction_date,
    (t->>'amount')::numeric as amount,
    t->>'account' as account_code
FROM properties p,
     jsonb_array_elements(p.external_data->'financials'->'transactions_2024') as t
WHERE p.external_data->'financials'->'transactions_2024' IS NOT NULL
ORDER BY (t->>'date')::date DESC
```

**Finn den største eiendommen (mest areal - direkte felt):**

```sql
SELECT property_id, name, address, total_area
FROM properties
WHERE total_area IS NOT NULL
ORDER BY total_area DESC
LIMIT 1
```

**Finn eiendommer sortert etter størrelse:**

```sql
SELECT name, address, total_area, city
FROM properties
WHERE total_area IS NOT NULL
ORDER BY total_area DESC
LIMIT 10
```

**Eiendommer i en region (f.eks. Sør) med navn som inneholder et ord (f.eks. barnevern):**
Bruk `region ILIKE '%X%'` for region (verdier kan være "Region Sør", "Sør", "02 - Øst" osv.) og `name ILIKE '%Y%'` for navn.

```sql

SELECT name, address, city, region
FROM properties
WHERE region ILIKE '%Sør%' AND name ILIKE '%barnevern%'
ORDER BY name
LIMIT 50

```

### Aggregering med JSONB

**Gjennomsnittlig leie per region:**

```sql

SELECT 
    p.region,
    AVG((c.amount->>'amount_per_year')::numeric) as avg_yearly_rent,
    COUNT(*) as contract_count
FROM contracts c
JOIN units u ON c.unit_id = u.unit_id
JOIN properties p ON u.property_id = p.property_id
WHERE c.status = 'active'
  AND c.amount->>'amount_per_year' IS NOT NULL
GROUP BY p.region
ORDER BY avg_yearly_rent DESC

```

**Sammenlign kostnad per kvm på tvers av regioner:**

```sql

SELECT 
    p.region,
    COUNT(p.property_id) as antall_eiendommer,
    ROUND(AVG((COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
         + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)) 
         / NULLIF(p.total_area, 0))::numeric, 2) as avg_cost_per_sqm,
    SUM((COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
         + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)))::bigint as total_cost
FROM properties p
WHERE p.total_area IS NOT NULL 
  AND p.total_area > 0
  AND p.external_data->'financials' IS NOT NULL
GROUP BY p.region
ORDER BY avg_cost_per_sqm DESC

```

**Total vedlikeholdskostnad per region:**

```sql

SELECT 
    p.region,
    COUNT(p.property_id) as antall_eiendommer,
    SUM((COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
         + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)))::bigint as total_maintenance_cost,
    ROUND(AVG((COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
         + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)))::numeric, 0) as avg_cost_per_property
FROM properties p
WHERE p.external_data->'financials' IS NOT NULL
GROUP BY p.region
ORDER BY total_maintenance_cost DESC

```

**Topp 3 eiendommer med høyest kostnad per kvm i hver region:**

```sql
WITH ranked_properties AS (
    SELECT 
        p.name,
        p.address,
        p.region,
        p.total_area,
        (COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
         + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)) as total_cost,
        ROUND(((COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
         + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)) 
         / NULLIF(p.total_area, 0))::numeric, 2) as cost_per_sqm,
        ROW_NUMBER() OVER (PARTITION BY p.region ORDER BY 
            ((COALESCE((p.external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
             + COALESCE((p.external_data->'financials'->>'total_spend_csv')::numeric, 0)) 
             / NULLIF(p.total_area, 0)) DESC) as rank
    FROM properties p
    WHERE p.total_area IS NOT NULL 
      AND p.total_area > 0
      AND p.external_data->'financials' IS NOT NULL
)
SELECT name, address, region, total_area, total_cost, cost_per_sqm
FROM ranked_properties
WHERE rank <= 3
ORDER BY region, rank
```

**Total kostnad per kategori fra external_data:**

```sql
SELECT 
    p.region,
    SUM((p.external_data->'financials'->>'total_manual_expenses')::numeric) as total_expenses
FROM properties p
WHERE p.external_data->'financials'->>'total_manual_expenses' IS NOT NULL
GROUP BY p.region
```

**Eiendommer with høyest kostnad per kvm (cost_summary / total_area):**

```sql
SELECT 
    p.name,
    p.address,
    p.total_area,
    (p.external_data->'financials'->>'cost_summary')::numeric as total_cost,
    ROUND(((p.external_data->'financials'->>'cost_summary')::numeric / p.total_area)::numeric, 2) as cost_per_sqm
FROM properties p
WHERE p.total_area IS NOT NULL 
  AND p.total_area > 0
  AND p.external_data->'financials'->>'cost_summary' IS NOT NULL
ORDER BY cost_per_sqm DESC
LIMIT 10
```

**Eiendommer med høyest leie per kvm (basert på kontrakter):**

```sql
SELECT 
    p.name,
    p.address,
    p.total_area,
    SUM((c.amount->>'amount_per_year')::numeric) as total_rent,
    ROUND((SUM((c.amount->>'amount_per_year')::numeric) / p.total_area)::numeric, 2) as rent_per_sqm
FROM properties p
JOIN units u ON u.property_id = p.property_id
JOIN contracts c ON c.unit_id = u.unit_id
WHERE p.total_area IS NOT NULL 
  AND p.total_area > 0
  AND c.status = 'active'
  AND c.amount->>'amount_per_year' IS NOT NULL
GROUP BY p.property_id, p.name, p.address, p.total_area
ORDER BY rent_per_sqm DESC
LIMIT 10
```

**Største eiendommer med lav husleie (sortert på areal synkende, deretter lavest husleie per kvm):**

```sql
SELECT 
    p.name,
    p.total_area,
    p.region,
    COALESCE(SUM((c.amount->>'amount_per_year')::numeric), 0)::bigint AS husleie_ar,
    ROUND((COALESCE(SUM((c.amount->>'amount_per_year')::numeric), 0) / NULLIF(p.total_area, 0))::numeric, 0) AS kr_per_kvm
FROM properties p
LEFT JOIN units u ON u.property_id = p.property_id
LEFT JOIN contracts c ON c.unit_id = u.unit_id AND c.status = 'active' AND c.amount->>'amount_per_year' IS NOT NULL
WHERE p.total_area > 0
GROUP BY p.property_id, p.name, p.total_area, p.region
HAVING COALESCE(SUM((c.amount->>'amount_per_year')::numeric), 0) > 0
ORDER BY p.total_area DESC, kr_per_kvm ASC
LIMIT 12
```

**Topp parter/firmaer etter totalt kontraktsbeløp (hvilket firma har størst kostnad/avtale):**

```sql
SELECT 
    pt.name AS party_name,
    pt.orgnr,
    SUM((c.amount->>'amount_per_year')::numeric) AS total_amount,
    COUNT(c.contract_id) AS contract_count
FROM parties pt
JOIN contracts c ON c.party_id = pt.party_id
WHERE c.status = 'active'
  AND c.amount->>'amount_per_year' IS NOT NULL
GROUP BY pt.party_id, pt.name, pt.orgnr
ORDER BY total_amount DESC
LIMIT 10
```

**Eiendommer med høyest vedlikeholdskostnad (fra external_data):**

```sql
SELECT 
    name,
    address,
    (COALESCE((external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
     + COALESCE((external_data->'financials'->>'total_spend_csv')::numeric, 0)) AS total_cost
FROM properties
WHERE external_data->'financials' IS NOT NULL
ORDER BY total_cost DESC
LIMIT 10
```

**Antall åpne avvik per eiendom:**

```sql
SELECT p.name, COUNT(c.case_id) as open_cases
FROM internal_control_cases c
JOIN properties p ON c.property_id = p.property_id
WHERE c.status != 'closed'
GROUP BY p.property_id, p.name
ORDER BY open_cases DESC
```

**Totalt antall avvik i hele porteføljen (totalt):**

```sql
SELECT status, COUNT(*) as count
FROM internal_control_cases
GROUP BY status
```

**Finn alle kritiske avvik:**

```sql
SELECT p.name, c.title, c.due_date
FROM internal_control_cases c
JOIN properties p ON c.property_id = p.property_id
WHERE c.priority = 'critical' AND c.status != 'closed'
```

**Eiendommer med høyest kostnad per kvadratmeter (vedlikehold per kvm):**

```sql
SELECT 
    name,
    address,
    total_area,
    (COALESCE((external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
     + COALESCE((external_data->'financials'->>'total_spend_csv')::numeric, 0)) AS total_cost,
    ROUND(((COALESCE((external_data->'financials'->>'total_manual_expenses')::numeric, 0) 
     + COALESCE((external_data->'financials'->>'total_spend_csv')::numeric, 0)) / NULLIF(total_area, 0))::numeric, 2) AS cost_per_sqm
FROM properties
WHERE total_area IS NOT NULL AND total_area > 0
ORDER BY cost_per_sqm DESC
LIMIT 10
```
