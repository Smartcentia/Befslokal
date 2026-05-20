# Steg for å fylle inn manglende utgifter (69 eiendommer)

Denne guiden beskriver konkrete steg for å få på plass løpende utgifter for alle eiendommer som i dag har **0** utgiftsposter i `external_data.financials.manual_expenses`.

---

## Slik kjører du scriptene fra terminalen

Åpne terminal og gå til prosjektmappen (der `backend/` ligger). Bruk **python3**.

**1) Sjekk manglende / for mange utgifter**
```bash
cd backend
python3 scripts/sjekk_utgifter_eiendommer.py
```

**2) Sjekk duplikater (rapport – endrer ikke DB)**
```bash
cd backend
python3 scripts/sjekk_utgiftsduplikater.py
```

**3) Fjerne duplikater (oppdaterer DB)**
```bash
cd backend
python3 scripts/remove_financial_duplicates.py
```

Krav: `backend/.env` må ha `DATABASE_URL` satt (Postgres). Kjør alltid fra `backend`-mappen slik at scriptene finner `.env` og modulene.

---

## Oversikt

- **Kjør sjekk:** `cd backend && python3 scripts/sjekk_utgifter_eiendommer.py`  
  → Gir oppdatert liste over eiendommer uten utgifter og deres `property_id`.

- **Datakilder:**  
  1. Reimport fra `backend/docs/*.txt` (samme kilde som brukes i `reimport_all_financials_v2.py`)  
  2. CSV/Excel du har med utgifter per eiendom  
  3. Manuell registrering via API / KI-kollega / MCP-verktøy

---

## Steg 1: Identifiser de 69 eiendommer

1. Fra prosjektrot:  
   `cd backend && python3 scripts/sjekk_utgifter_eiendommer.py`

2. I utskriften: under **«Eiendommer UTEN løpende utgifter»** står navn, adresse og `property_id` for hver eiendom.

3. (Valgfritt) Lag en liste med `property_id` for senere bruk, f.eks.:  
   - Kopier `property_id`-linjene fra utskriften til en fil, eller  
   - Etterpå kan du eksportere fra DB med et enkelt SQL/script som henter alle der `jsonb_array_length((external_data->'financials'->'manual_expenses')::jsonb) = 0` eller tilsvarende.

---

## Steg 2: Velg datakilde og metode

### Alternativ A: Reimport fra docs (anbefalt hvis data finnes der)

Utgiftsdata ligger i `backend/docs/` som filer `01.txt`–`17.txt` og `1A.txt`. Scriptet matcher eiendomsnavn i filene mot `properties.name` i databasen.

1. **Sjekk at docs ligger på plass**  
   - `backend/docs/01.txt` … `17.txt`, `1A.txt` (eller de filer som `reimport_all_financials_v2.py` er satt opp til).

2. **Kjør reimport (uten å tømme eksisterende først, hvis du bare vil fylle hull)**  
   - I dagens script tømmes alle financials først. For **kun** å fylle inn manglende, må du enten:  
     - bruke en **modifisert** versjon som **ikke** kjører `clear_existing_financials()` og som **kun** oppdaterer eiendommer som har 0 utgifter, eller  
     - kjøre full reimport (clear + import) hvis det er akseptabelt å overskrive alle finansdata.

3. **Kjør fra backend-mappen:**  
   `python3 scripts/reimport_all_financials_v2.py`  
   (Krever at `docs`-mappen ligger under `backend/` eller at `DOCS_DIR` i scriptet peker dit.)

4. **Sjekk «unmatched»-loggen**  
   - Eiendommer som fortsatt ikke får utgifter etter reimport, vil ofte havne i scriptets unmatched-logg.  
   - For de 69: sammenlign navn i DB med navn i txt-filene. Juster enten eiendomsnavn i DB eller teksten i docs (eller matchelogikken) slik at de 69 også matcher ved neste kjøring.

5. **Verifiser:** Kjør `sjekk_utgifter_eiendommer.py` på nytt – antall uten utgifter bør ha gått ned.

---

### Alternativ B: CSV/Excel med utgifter

Hvis du har en fil (CSV/Excel) med utgifter per eiendom:

1. **Format** (minst):  
   - Identifikator for eiendom: `property_id` (UUID) eller entydig `eiendomsnavn` / `adresse`.  
   - Utgift: f.eks. `kategori`/`type`, `beløp`, `leverandør`, `dato`.

2. **Lag et lite importscript** som:  
   - Leser CSV/Excel.  
   - For hver rad: finn `property_id` (via navn/adresse mot DB om nødvendig).  
   - Kaller enten:  
     - Backend-API for å legge til utgift (f.eks. `POST …/finans/expense` med `property_id`, `type`, `amount`, `provider`, `date`), eller  
     - Oppdaterer `external_data` direkte (som i `reimport_all_financials_v2.py`): les property, hent `financials.manual_expenses`, append ny post, oppdater `total_manual_expenses`, lagre.

3. **Kjør importen** kun for de 69 (filtrer på listen fra Steg 1).

4. **Verifiser:** Kjør `sjekk_utgifter_eiendommer.py` igjen.

---

### Alternativ C: Manuell registrering

For enkelt-eiendommer eller når du ikke har bulkdata:

1. **Via API** (hvis tilgjengelig):  
   - `POST` mot finans-endepunkt med `property_id`, `type`, `amount`, evt. `provider`, `date`, `description`.

2. **Via KI-kollega / MCP:**  
   - Bruk verktøyet som kaller `finans_add_expense` med `property_id`, `type`, `amount`, osv.

3. **Én og én:**  
   - For hver av de 69: finn eiendom i appen, legg inn utgifter der det finnes grensesnitt, eller bruk API/MCP som over.

---

## Steg 3: Fokus på de 69

- Uansett metode: **filtrer eller fokuser på de 69** eiendommer fra Steg 1 (f.eks. les listen med `property_id` og bare oppdater disse i scriptet eller i reimport-logikken).
- Ved reimport fra docs: Etter kjøring, sjekk om noen av de 69 fortsatt står i «Eiendommer UTEN utgifter». De som fortsatt mangler, må løses med forbedret matching (navn i docs vs. DB) eller med CSV/manuell metode.

---

## Steg 4: Verifisering

1. Kjør:  
   `cd backend && python3 scripts/sjekk_utgifter_eiendommer.py`

2. Sjekk at **«Eiendommer uten utgifter»** er redusert (helst 0 for de du har fylt inn).

3. (Valgfritt) Sjekk noen eiendommer i appen at utgiftene vises korrekt.

---

## Kort oppsummert

| Steg | Handling |
|------|----------|
| 1 | Kjør `sjekk_utgifter_eiendommer.py` og noter de 69 (navn + `property_id`). |
| 2 | Velg A (reimport fra docs), B (CSV/Excel) eller C (manuell/API/MCP). |
| 3 | Kjør import kun for de 69 der det er mulig; for reimport, juster matching for de som fortsatt ikke matcher. |
| 4 | Kjør sjekk-scriptet på nytt og evt. visuell sjekk i appen. |

---

## Duplikatsjekk etterpå

Når utgifter er fylt inn, kan du kjøre duplikatsjekk for eiendommer med mange poster:

- Rapport (kun sjekk):  
  `cd backend && python3 scripts/sjekk_utgiftsduplikater.py`  
- Fjerne duplikater:  
  `cd backend && python3 scripts/remove_financial_duplicates.py`  
  (Bruk evt. først rapport-scriptet for å se om det er duplikater.)

Rapport-scriptet beskrives nedenfor under «Duplikatsjekk».
