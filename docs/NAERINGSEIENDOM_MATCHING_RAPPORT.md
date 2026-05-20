# Næringseiendom – matching og status

**Full liste over eiendommer:** [docs/NAERINGSEIENDOM_EIENDOMSLISTE.md](NAERINGSEIENDOM_EIENDOMSLISTE.md) – alle som vises som næringseiendom, kategorisert (uten kobling / med parent_unit_id_erp uten forelder / Avdeling uten match).

## Data hentet via Supabase CLI (linket prosjekt «BEF EIENDOM»)

**Tabellstatistikk** (supabase inspect db table-stats --linked):

| Tabell      | Estimat antall rader |
|------------|------------------------|
| properties | 603                    |
| units      | 222                    |
| contracts  | 405                    |
| parties    | 114                    |

## Hvordan matching fungerer

Parent-eiendom (avdeling → institusjon) settes i API når:

1. **Strategi 1:** `property.parent_unit_id_erp` er satt og en annen eiendom har `unit_id_erp` = den verdien → `parent_property_id` satt.
2. **Strategi 2:** `property.unit_short_type == "Avdeling"` og eiendom har `affiliation` + `region`, og en eiendom med `unit_short_type == "Barnevernsinstitusjon"` har samme (affiliation, region) → `parent_property_id` satt.

Eiendommer som kun har `usage = Næringseiendom` (eller default) uten disse feltene får aldri `parent_property_id`.

## Full diagnostikk (næringseiendom med/uten kobling)

Kjør lokalt med database-tilkobling (DATABASE_URL i `backend/.env` eller `railway run`):

```bash
cd backend && python3 scripts/sjekk_naeringseiendom_matching.py
```

Scriptet viser:

- Totalt antall eiendommer og antall som vises som næringseiendom.
- Antall matchet via parent_unit_id_erp (med/uten treff).
- Antall matchet via Avdeling + affiliation + region (med/uten treff).
- Antall uten kobling (kandidater for manuell matching).
- Eksempelrader på eiendommer uten kobling.

## Bruk av Supabase CLI

- **Tabellstatistikk:** `supabase inspect db table-stats --linked -o pretty`
- **Prosjekt:** Linket prosjekt er «BEF EIENDOM» (ref: vwvhxcqxadblrftuvsds).
- **Ad-hoc SQL:** Supabase CLI har ikke en `execute_sql`-kommando mot remote. For egendefinerte spørringer bruk scriptet over med DATABASE_URL (Session Pooler-URL fra Supabase Dashboard), eller kjør `psql` med samme URL.
