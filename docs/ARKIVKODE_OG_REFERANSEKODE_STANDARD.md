# Arkivkode og referansekode – standard for BEFS

Alle kontrakter, leietakere (parties) og kontraktstyper skal følge et enhetlig oppsett med egne referansekoder.

---

## 1. Kontrakter – arkivkode

### Format

```
BUF-[LOK]-[YYYYMMDD]-[NN]
```

| Del | Beskrivelse | Eksempel |
|-----|-------------|----------|
| BUF | Fast prefiks (Bufetat) | BUF |
| LOK | Lokaliseringkode (4–5 siffer) | 6125, 4711 |
| YYYYMMDD | Kontraktsdato (start eller signering) | 20241014 |
| NN | Løpenummer (01–99) per eiendom/dato | 01 |

**Eksempel:** `BUF-6125-20241014-01`

### Regler

- **Unik:** Én arkivkode per kontrakt. Ved flere kontrakter samme dag på samme eiendom: 01, 02, 03 …
- **Kilde:** Ved import fra Eie1212/Oversikt bygg: bruk `lokalisering_id` fra eiendom + `start_date` eller `signed_at` + løpenummer.
- **Legacy:** Statsbygg-nummer (04-12030-14) og Elements (2023/72720-14) lagres i `external_data` som referanse, men **arkivkode** er primær identifikator i BEFS.

### Database

| Tabell | Felt | Type | Unik |
|--------|------|------|------|
| contracts | `archive_code` | String(50) | Ja (unique index) |

---

## 2. Kontraktstyper (category) – enhetlig oppsett

| Kode | Beskrivelse |
|------|--------------|
| Leiekontrakt | Hovedleiekontrakt for lokaler |
| Tilleggskontrakt | Tillegg til hovedkontrakt |
| Serviceavtale | Vaktmester, renhold, andre tjenester |
| Parkeringsavtale | Kun parkering |
| Annet | Ikke kategorisert |

**Mapping fra kilder:**

| Kildeverdi | BEFS category |
|------------|----------------|
| Leiekontrakt, Leieavtale, Hovedkontrakt | Leiekontrakt |
| Tilleggskontrakt, Tillegg | Tilleggskontrakt |
| Serviceavtale, Vaktmester, Renhold | Serviceavtale |
| Parkeringsavtale, Parkering | Parkeringsavtale |
| Konkurranse, Kravspes., Fil mangler, … | Annet |

---

## 3. Leietakere / utleiere (parties) – referansekode

### Format

```
BUF-P-[NNNNNN]
```

| Del | Beskrivelse | Eksempel |
|-----|-------------|----------|
| BUF | Fast prefiks | BUF |
| P | Parti/Party | P |
| NNNNNN | 6-sifret løpenummer (000001–999999) | 000001 |

**Eksempel:** `BUF-P-000001`, `BUF-P-000042`

### Regler

- **Unik:** Én referansekode per party.
- **Generering:** Ved første import: tildel sekvensielt. Ved orgnr-match: gjenbruk eksisterende referansekode.
- **Orgnr:** `orgnr` (9 siffer) forblir unik for norske selskaper; `reference_code` er BEFS-internt arkiv/referansenummer.

### Database

| Tabell | Felt | Type | Unik |
|--------|------|------|------|
| parties | `reference_code` | String(20) | Ja (unique index) |

---

## 4. Implementasjon

### Nye kolonner

- `contracts.archive_code` (String, unique, nullable inntil migrering)
- `parties.reference_code` (String, unique, nullable inntil migrering)

### Import

- **import_master_data.py:** Generer `archive_code` for nye kontrakter, `reference_code` for nye parties.
- **import_oversikt_bygg_eiendom_csv.py:** Oppdater eksisterende kontrakter med arkivkode hvis mangler.
- **Fil-scanning:** Matching kan fortsatt bruke `external_data.contract_number` (Statsbygg) for fil-til-kontrakt; arkivkode brukes i UI og rapporter.

### Vedlikehold

- Ved manuell opprettelse: system genererer arkivkode/referansekode automatisk.
- Script for å backfylle eksisterende rader: `scripts/backfill_archive_and_reference_codes.py`.
