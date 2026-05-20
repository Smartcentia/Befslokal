# Regnskapsrevisjon 2020–2025 (metode og rapportmal)

Dette dokumentet beskriver **hvordan** BEFS kan verifisere at `gl_transactions` er knyttet til riktig eiendom, avdekke dobbeltføringer, og **sanity-sjekke** 2025 mot aggregerte tall i `property_annual_costs`.

## Automatisert rapport

Kjør (med gyldig `DATABASE_URL` i `backend/.env`, tilgjengelig fra ditt nettverk):

```bash
cd backend
source .venv/bin/activate   # eller bruk .venv/bin/python
python -m scripts.audit_gl_properties_2020_2025 --output ../docs/REGNSKAP_REVISJON_KJORT.md
```

Scriptet skriver Markdown til stdout og valgfritt til fil. Det dekker:

| Seksjon | Innhold |
|--------|---------|
| 1 | Volum per år: antall rader, % uten `property_id`, syntetiske rader, sum `amount`, kilder |
| 2 | Fordeling på `data_source` / `source_system` |
| 3 | Rader uten eiendom, med eksempel på `department_name` |
| 4 | Avvik der `gl_transactions.department_code` ≠ `properties.department_code` (når begge er satt) |
| 5 | Dobbeltføringer: samme `property_id` + `invoice_number` + `period` + `amount` |
| 6 | Samme faktura nøkkel fordelt på **flere** eiendommer |
| 7 | Mulige duplikater **uten** fakturanummer (streng nøkkel – kan ha falske positiver) |
| 8 | 2025: sammenligning mellom summerte felt i `property_annual_costs` og GL (se nedenfor) |
| 9 | Orphan `property_id` (skal være 0 med FK) |

## Viktige forbehold

1. **Tegn på beløp:** I skjemaet er kostnader ofte **negative** `amount`. Scriptet bruker `-SUM(negative)` som «kostnad som positive tall» i avstemmingen.
2. **Aggregerte 2025-tall** ligger i `property_annual_costs` (år 2025): bl.a. `kpi_adjusted_rent`, `internal_maintenance`, `common_costs`, `energy_costs`, `heating_costs`, `cleaning_costs`, `parking_rent`, `caretaker_cost`, `card_reader_cost`. Summen av disse er **ikke** identisk med hovedbok per definisjon (kontoplan, periodisering, internfakturering), men **store avvik per eiendom** bør undersøkes.
3. **Husleie i GL:** Positiv `amount` med `account_name` som matcher «Leie …» / «Husleie» inngår i egen kolonne i avstemmingen; dette speiler praksis i `scripts/avstem_husleie_mot_csv_2025.py`, men er ikke full lik `is_lease_account()` (f.eks. «Fellesutgifter …»).
4. **Import 2025 Midt:** `app/scripts/import_gl_2025.py` kobler koststed → `properties.unit_id_erp`. Feil `unit_id_erp` på eiendommen gir systematisk feil kobling.
5. **Syntetiske rader:** `is_synthetic = true` kan påvirke summer; vurder å filtrere ut i rapporter eller sammenligne med/uten.

## Manuell oppfølging (anbefalt)

- **CSV «Innkjøpsanalyse» 2025:** Bruk `python -m scripts.avstem_husleie_mot_csv_2025 --csv <fil>` for regional husleie-avstemming.
- **Enkelt eiendom:** API `GET /api/v1/accounting/transactions?property_id=…&year=…` eller direkte SQL mot `gl_transactions`.

## Resultat fra denne økten

> *Miljøet som kjørte analysen hadde ikke stabil tilgang til databasen (vertnavn/tidsavbrudd). Kjør kommandoen over lokalt eller fra et miljø med nettverkstilgang til Postgres for faktiske tall.*

Etter kjøring: lim inn eller commit `docs/REGNSKAP_REVISJON_KJORT.md` som endelig datarapport.
