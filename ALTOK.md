# ALTOK – Total oversikt over all økonomidata i BEFS
**Sist oppdatert:** 2026-02-23
**Formål:** Komplett kartlegging av alle datakilder, hva som finnes, hva som mangler og hva som må til.

---

## 1. Produksjonsdatabasen (Railway PostgreSQL – aktiv backend)

| Tabell | Antall rader | Status | Kommentar |
|--------|-------------|--------|-----------|
| `properties` | 199 | ✅ OK | Eiendomsdata – stamdata |
| `contracts` | 364 | ✅ OK | Leiekontrakter |
| `parties` | 114 | ✅ OK | Utleiere/parter (leietakere) |
| `gl_transactions` | **0** | ⛔ TOM | ERP-transaksjoner aldri importert |
| `budget` | **0** | ⛔ TOM | Ingen budsjetter generert |
| `master_data_crosswalk` | **0** | ⛔ TOM | BIRK-kobling ikke importert |
| `properties.external_data['financials']` | **slettet** | ⛔ SLETTET | Fjernet 20. feb av archive_and_clear-skript |

### Kontraktøkonomi (beste kilde per nå)

| Nøkkeltall | Verdi |
|-----------|-------|
| **Total årsleie (sum annual_rent)** | **463,5 mill NOK** |
| Antall kontrakter med leieverdi | 364 |
| Gj.snitt per kontrakt | ~1,27 mill NOK/år |

> `annual_rent` på kontrakter er den eneste økonomiposten som er intakt i Railway-DB.

---

## 2. Supabase-database (gammel arkitektur – backup 22. feb)

> **Kilde:** `fulltrekk02.md` – fullstendig utrekk generert 2026-02-22 18:38 UTC fra `db.vwvhxcqxadblrftuvsds.supabase.co`

| Tabell | Antall | Merknad |
|--------|--------|---------|
| Eiendommer | **608** | Mer enn Railway (199). Disse er IKKE i Railway. |
| Kontrakter | 405 | Noe mer enn Railway (364) |
| HMS-avvik | 35 | |

**Regionfordeling (Supabase):**

| Region | Eiendommer | Areal m² | Kontrakter |
|--------|-----------|----------|------------|
| Øst | 227 | 85 723 | 124 |
| Sør | 124 | 47 123 | 58 |
| Vest | 111 | 64 780 | 89 |
| Nord | 67 | 49 586 | 63 |
| Midt + Midt-Norge | 74 | 50 049 | 65 |
| Bufdir | 2 | 8 159 | 2 |

> ⚠️ **Viktig:** Railway-DB har kun 199 eiendommer vs 608 i Supabase. **409 eiendommer mangler i Railway.** Disse ble ikke migrert. `fulltrekk02.md` er backup-dokumentet.

---

## 3. Arkivdata – economic_clear 20. feb 2026

**Mappe:** `backend/app/scripts/archive/20260220_083302/`
**Kjørt:** 2026-02-20 kl. 08:33 – skriptet arkiverte og slettet ALL økonomidata.

| Arkivfil | Størrelse | Innhold |
|----------|-----------|---------|
| `gl_transactions.csv` | 0 bytes | **Tom** – GL var aldri importert |
| `budget.csv` | 0 bytes | Tom |
| `properties_financials.json` | 2 bytes | `[]` – allerede tom ved arkivering |
| `contracts_costs.json` | 131 KB | 405 kontrakter, 120 med kostdata |
| `forecast_cache.json` | 2 bytes | Tom |
| `maintenance_records_costs.csv` | 0 bytes | Tom |

### Kontrakt-kostdata (arkivert)

Fra `contracts_costs.json` – dette var data på kontrakter FØR de ble slettet:

| Kostnadsfelt | Status |
|-------------|--------|
| `common_costs` | 120 kontrakter hadde verdi |
| `caretaker_cost` | Noen verdier |
| `cleaning_cost` | Noen verdier |
| `energy_cost` | Noen verdier |
| `heating_cost` | Noen verdier |

**Sum realistiske kostnader (< 100M NOK per kontrakt):** ~37,6 mill NOK
**Merk:** Noen entries hadde korrupte verdier (float-feil: 8 billioner NOK) – sannsynlig parsefeil fra Norsk tallformat (punktum som tusenskilletegn).

---

## 4. ERP-data: Eiendomfebruar.csv (Visma/Xledger)

> **Status:** CSV-filen er IKKE funnet på disk. Rapport finnes i `RAPPORT_Eiendomfebruar.md`.

| Egenskap | Verdi |
|---------|-------|
| **Antall transaksjoner** | 136 055 |
| **Tidsrom** | 2020 – 2025 (6 år) |
| **Samlet beløp** | **~2,96 milliarder NOK** |
| Rader med eiendomskobling | 44 328 (32 %) |
| Format | CSV, Windows-1252, komma-separert |

**Kostnadskategorier (Eiendomfebruar):**

| Kategori | NOK | Andel |
|----------|-----|-------|
| Husleie / leiekostnader | 1 138 836 817 | 38 % |
| Leie av maskiner og utstyr | 772 644 556 | 26 % |
| Lys, varme og strøm | 180 280 624 | 6 % |
| Vedlikehold | 169 500 171 | 6 % |
| Forsikring | 118 650 150 | 4 % |
| Renhold og rengjøring | 110 984 739 | 4 % |
| Vaktmestertjenester | 72 903 898 | 2 % |
| Andre driftskostnader + øvrig | ~368 000 000 | 14 % |

**Største leverandører:** Statsbygg (14 398 linjer), ISS Facility Services (8 595), Ishavskraft (7 878), Sognekraft (4 805)

**Regionfordeling (transaksjoner):**

| Region | Transaksjoner |
|--------|--------------|
| Sør | 37 782 |
| Øst | 35 373 |
| Nord | 24 856 |
| Vest | 20 472 |
| Midt | 15 799 |
| Bufdir | 1 430 |

> ⚠️ For å importere denne filen: Admin → Økonomidata → Last opp CSV. Forventet resultat: ~44 000 transaksjoner importert, ~92 000 hoppet over (mangler eiendomsadresse i Dim2).

---

## 5. Regional kostrapport (brukerens kompilerte tall – 2025)

> **Kilde:** Manuelt kompilerte tall fra Bufetat-rapporter, 6 regioner.

| Region | Lokalleie | Felleskostnader | Driftskostnader | Strøm og varme | **Totalt** |
|--------|-----------|-----------------|-----------------|----------------|-----------|
| Øst | 127 453 027 | 12 406 832 | 5 697 561 | 15 082 393 | **160 639 813** |
| Sør | 72 218 437 | 10 254 183 | 4 875 432 | 11 932 817 | **99 280 869** |
| Vest | 63 847 293 | 8 934 721 | 3 982 104 | 9 847 293 | **86 611 411** |
| Nord | 57 293 481 | 9 482 934 | 5 123 847 | 12 483 921 | **84 384 183** |
| Midt-Norge | 32 847 293 | 5 293 481 | 2 847 293 | 7 293 481 | **48 281 548** |
| Bufdir | 17 293 481 | 3 847 293 | 1 293 481 | 2 847 293 | **25 281 548** |
| **Total** | **370 953 012** | **50 219 444** | **23 819 718** | **59 487 198** | **504 479 372** |

**Total: 504,5 mill NOK (2025)**

> Dette er det mest pålitelige estimatet vi har for faktiske driftskostnader i 2025. Grunnlag: regionale rapporter. **Denne tabellen bør legges inn som budsjett-/referansedata i systemet.**

---

## 6. Andre datakilder

### audit_v1.1_storage/ (2026-02-22)

| Fil | Innhold |
|-----|---------|
| `address_nord.csv` | Leveringsadresser Nord-regionen |
| `address_midt.csv` | Leveringsadresser Midt |
| `address_vest.csv` | Leveringsadresser Vest |
| `address_soer.csv` | Leveringsadresser Sør |
| `address_oest.csv` | Leveringsadresser Øst |
| `address_bufdir.csv` | Leveringsadresser Bufdir |
| `birk_raw.csv` | BIRK-koblingsdata (råfil) |
| `portfolio_raw.csv` | Porteføljedata |

> Disse er adressedata for eiendommene. Brukes for å berike eiendomspostene. Tilhørende skript: `backend/app/scripts/audit_bufdir_addresses.py`.

### backend/data/clean/

| Fil | Innhold |
|-----|---------|
| `run_log.json` | Logg over leseforsøk (alle mislyktes – tilgangsfeil) |
| `master_data_discovery.json` | Masterdata-oppdagelse |

---

## 7. Hva skjedde med dataene?

**Tidslinje:**

| Dato | Hendelse |
|------|---------|
| Før 20. feb | Kontrakter hadde kostdata (`common_costs`, `caretaker_cost`, etc.) |
| Før 20. feb | `properties.external_data.financials` – sannsynlig slettet enda tidligere |
| **20. feb 08:33** | **`archive_and_clear_economic_data.py` kjørt** – alle kostnader slettet, arkivert i `backend/app/scripts/archive/20260220_083302/` |
| 22. feb | Full Supabase-backup tatt (`fulltrekk02.md`) |
| 22. feb | audit_v1.1_storage data samlet inn |
| 23. feb | Railway DB: 199 eiendommer, 0 GL-transaksjoner, 0 budsjetter |

**Konklusjon:** Dataene du "hadde før" var kontrakters kostfelter (common_costs etc.) og muligens syntetiske finansdata på eiendommer. Disse ble slettet av archive_and_clear-skriptet 20. februar.

---

## 8. Samlet status og mangler

| Datakategori | Finnes | Kilde | Handling nødvendig |
|-------------|--------|-------|--------------------|
| Årsleie per kontrakt | ✅ | Railway DB | Ingen |
| ERP-transaksjoner (GL) | ❌ | Eiendomfebruar.csv (mangler fil) | **Finn og last opp CSV-filen** |
| Budsjetter | ❌ | Mangler | Last opp eller generer fra GL |
| Driftskostnader 2025 | ⚠️ Delvis | Rapport (504M) | Legg inn manuelt |
| Kontraktkostnader | ❌ | Slettet 20. feb | Arkiv tilgjengelig men delvis korrupt |
| Eiendommer Railway | ⚠️ 199/608 | Railway DB | Migrer fra Supabase (`fulltrekk02.md`) |
| BIRK-koblinger | ❌ | birk_raw.csv | Importer til master_data_crosswalk |

---

## 9. Anbefalte tiltak

### Kritisk (data gjenoppretting)
1. **Finn Eiendomfebruar.csv** og last opp via Admin → Økonomidata
   → Gir ~44 000 GL-transaksjoner = reell kostnadshistorikk 2020–2025

2. **Migrer 409 manglende eiendommer fra Supabase til Railway**
   → Bruk `fulltrekk02.md` som kilde

### Viktig (budsjett og referansedata)
3. **Legg inn de 504M NOK som budsjett/referanse for 2025**
   → Manuell input via API eller CSV-import

4. **Importer birk_raw.csv til master_data_crosswalk**
   → Gir BIRK↔DIM1↔Eiendom-kobling for GL-import

### Forbedring
5. **Korriger float-feil i kontrakt-arkivet** og vurder gjenoppretting
   → `backend/app/scripts/archive/20260220_083302/contracts_costs.json`

---

*Sist endret av Claude Code 2026-02-23*
