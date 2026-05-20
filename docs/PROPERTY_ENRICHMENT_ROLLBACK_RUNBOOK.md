# Property Enrichment Rollback Runbook

Sist oppdatert: 2026-04-09
Omfang: property enrichment batch (dry-run/apply), admin-endepunkter og frontend admin-kontroller.

## 1. Formål

Denne runbooken beskriver hvordan vi:
- stopper videre skade ved feil i enrichment-kjøring,
- ruller tilbake kodeendringer trygt,
- gjenoppretter data fra backup/snapshot ved behov,
- verifiserer at systemet er friskt etter rollback.

## 2. Hva som kan rulles tilbake

- Kode: alltid reverserbart med `git revert`.
- Data (DB): krever backup/snapshot tatt før apply-kjøring.
- Filer (bilder): kan slettes selektivt i `frontend/public/bufdir_images` hvis de ble lagt til i en feilkjøring.

## 3. Preconditions før apply (obligatorisk)

1. Kjør dry-run først, aldri hopp direkte til apply.
2. Bekreft at rapporten ser riktig ut (delta for navn, beskrivelser, bilder).
3. Ta database-backup/snapshot rett før apply.
4. Noter følgende i change-logg:
   - tidspunkt,
   - kjørende bruker,
   - valgt terskel (`min_score`),
   - rapportfilnavn,
   - commit hash for deployet kode.

## 4. Incident levels

- L1: UI/API-feil uten dataendringer.
  - Tiltak: kode-revert/deploy.
- L2: apply ga feil data på et begrenset utvalg.
  - Tiltak: kode-revert + målrettet DB-restore (tabell/rader hvis mulig).
- L3: apply ga bred datakorrupt effekt.
  - Tiltak: kode-revert + full restore fra pre-apply snapshot.

## 5. Rask stopp ved feil (first response)

1. Stopp nye apply-kjøringer (operasjonell freeze).
2. Verifiser siste kjøring via report-endepunkt.
3. Kommuniser impact-vindu (fra `started_at` til `finished_at` i rapport).

## 6. Kode-rollback

Bruk non-destructive revert:

```bash
# i riktig branch/worktree
cd /path/to/BEFS_CLEAN

# eksempel: revert av enrichment-commit
git revert <ENRICHMENT_COMMIT_HASH>

# push branch og deploy normalt etter godkjenning
git push
```

Eksempel fra lokal historikk i denne sesjonen:
- enrichment commit: `c6cd0de4`

Obs:
- Ikke bruk `git reset --hard` i delt branch.
- Revert på branch som faktisk deployes (ikke feil worktree).

## 7. Data-rollback

### 7.1 Krav

Data-rollback forutsetter snapshot/backup tatt rett før apply.
Uten backup finnes ingen garantert full reversering.

### 7.2 Standardprosedyre

1. Identifiser pre-apply snapshot (timestamp før `started_at` i rapport).
2. Sett app i vedlikeholdsmodus/frys skriveoperasjoner.
3. Restore snapshot til ønsket miljø.
4. Kjør post-restore verifisering (seksjon 9).

### 7.3 Minimal skadebegrensning uten full restore

Hvis full restore ikke er mulig:
1. Bruk enrichment-rapportens `samples` + metadata til å finne berørte properties.
2. Reverser felter manuelt/med SQL-script:
   - `property.name`
   - `property.description`
   - `property.external_data.bufdir.*`
   - `property.external_data.providers`
3. Slett eventuelle feilaktig nedlastede bilder i `frontend/public/bufdir_images`.

## 8. Operasjonell rollback av kjøring

Anbefalt produksjonsflyt for å redusere blast radius:

1. Dry-run med pilot-limit (f.eks. 50).
2. Evaluer rapport.
3. Apply med samme terskler.
4. Hvis avvik oppdages: stopp, og gå til seksjon 5-7.

## 9. Verifisering etter rollback

Kjør minimum:

```bash
# backend
cd backend
.venv/bin/python -m pytest tests/admin -q

# frontend
cd ../frontend
npm run typecheck
npm run build
```

Verifiser i admin:
1. `/admin` laster.
2. Dry-run kan kjøres.
3. Report list/get fungerer.
4. Apply krever eksplisitt bekreftelse.

## 10. Ansvar og sign-off

Rollback er fullført når:
1. Teknisk ansvarlig bekrefter grønn teststatus.
2. Produkt/dataeier godkjenner datakvalitet etter rollback.
3. Incident-logg er oppdatert med root cause og preventive actions.

## 11. Operativ sjekkliste (kortversjon)

1. Freeze apply.
2. Finn siste rapport + impact-vindu.
3. Revert kode med `git revert`.
4. Restore DB fra pre-apply snapshot (eller målrettet reversering).
5. Verifiser tester + admin-flyt.
6. Dokumenter og signer av.
