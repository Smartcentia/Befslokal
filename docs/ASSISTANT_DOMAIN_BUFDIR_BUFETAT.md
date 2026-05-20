# Bufdir, Bufetat og BEFS (kontekst for assistenter)

Cursor injiserer automatisk [`.cursor/rules/bufdir-bufetat-domain.mdc`](../.cursor/rules/bufdir-bufetat-domain.mdc) (`alwaysApply: true`). Denne `docs/`-filen speiler innholdet for lesbarhet og lenker; ved endringer, oppdater **begge** eller bare regelen og kort noter her.

## Innhold (regeltekst)

- **Bufdir** (Barne-, ungdoms- og familiedirektoratet) er direktoratet under BFD; det **styrer Bufetat** og har bredt faglig mandat (barnevern, familievern, adopsjon, likestilling m.m.). Offisiell oversikt: [bufdir.no/om](https://www.bufdir.no/om/).
- **Bufetat** leverer **det statlige barne- og familievernet**, organisert i **fem regioner** (operasjonelt nivå for mange eiendommer og kontrakter).
- **BEFS/KNOWME** i dette repoet handler primært om **eiendom, enheter, kontrakter, økonomi, innkjøp og HMS** – ikke om enkeltbarnevernssaker eller personsensitive saksdata som kjerne domene.
- **Region i data:** `Bufdir` er **eget organisatorisk nivå**, ikke en geografisk region som Øst/Vest. Bruk canonical mapping og begreper i [`REGION_STANDARD.md`](REGION_STANDARD.md), [`BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md`](BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md) (kap. om Bufdir), og `backend/app/domains/core/utils/region_mapping.py`.

Ved import, rapportering og RBAC: skille **Bufetat-region** fra **Bufdir (direktorat)**, og ikke slå sammen med Viken/Oslo uten eksplisitt forretningsregel.
