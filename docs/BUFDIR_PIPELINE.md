# Bufdir-pipeline: data og bilder

## Hva som lastes ned og hvor

| Steg | Script | Krever DB | Hva som skjer |
|------|--------|-----------|----------------|
| 1 | `fetch_bufdir_data.py` | Nei | Henter **liste-data** fra bufdir.no (navn, adresse, beskrivelse, `image_url`, lovgrunnlag, e-post, telefon, sted). Lagrer i **backend/bufdir_institutions.json**. **Bilder lastes ikke ned her** – kun URL-er lagres. |
| 2 | `match_bufdir_robust.py` | Ja | Matcher institusjoner mot eiendommer i databasen. Skriver **backend/bufdir_matches_robust.json** (treff) og **backend/bufdir_unmatched.json** (uten treff). |
| 3 | `enrich_properties_bufdir.py` | Ja | For **matchade** eiendommer: laster ned **bilder** fra `image_url` til **frontend/public/bufdir_images/** og fyller **external_data.bufdir** (inkl. `image_path`) i databasen. |
| 4 | `establish_bufdir_unmatched.py` | Ja | For **umatchade** institusjoner: oppretter nye (syntetiske) eiendommer med bufdir-data, laster ned **bilder** til **frontend/public/bufdir_images/** og setter **external_data.bufdir** + **external_data.synthetic**. |
| 5 | `fetch_images_for_barnevern.py` | Ja | **Valgfritt:** For barnevernsinstitusjoner som fortsatt mangler bilde: bruker LLM (OpenAI) til å foreslå søkeord, søker på nettet (DuckDuckGo) og laster ned bilder. Krever `OPENAI_API_KEY` for LLM (ellers brukes enkle søkeord). Kjør: `./scripts/kjor_fetch_barnevern_images.sh` |

## Eiendomskvalitet (revisjon mot Bufdir)

| Script | Krever DB | Hva |
|--------|-----------|-----|
| `backend/scripts/audit_properties_quality_bufdir.py` | Ja | Leser **alle** eiendommer, sammenligner med **backend/bufdir_institutions.json** (samme kilde som bufdir.no-listen), finner bl.a. navn som ser ut som adresse, `address == name`, og avvik mellom lagret Bufdir-data og JSON. Skriver **backend/data/properties_quality_audit.md**. Valgfritt: `--apply-safe-fixes` / `--dry-run` for automatiske, konservative rettinger. |

Tidligere / spesialiserte sjekker: `sjekk_navn_kun_adresse.py` (kun adresse som navn), `fix_address_equals_name.py` (kun `address == name`), `app/scripts/audit_bufdir_addresses.py` (Bufdir-feltkontorer mot DB).

## Svar på: «Er alt data + bilder lastet ned eller brukes?»

- **Liste-data (alt vi trenger av tekst/URL-er):** Ja – det lastes ned og brukes i steg 1 (`fetch_bufdir_data.py`), uten database.
- **Bilder (faktiske filer):** Lastes først ned i steg 3 og 4. De **brukes** når frontend viser eiendomsdetalj (prioriterer `image_path`, ellers `image_url`). For at bildene faktisk skal **være lastet ned**, må du kjøre steg 2, 3 og 4 med **DATABASE_URL** satt (f.eks. via `.env`).

## DATABASE_URL og .env

Scriptene som trenger database (`match_bufdir_robust.py`, `enrich_properties_bufdir.py`, `establish_bufdir_unmatched.py`) laster nå **.env** automatisk fra `backend/.env` og prosjektrot, så **DATABASE_URL** trenger ikke eksporteres manuelt før kjøring.

Sørg for at du har `DATABASE_URL=...` i `.env` (i prosjektrot eller `backend/`), og kjør deretter:

```bash
cd /path/til/BEFS_CLEAN
python3 backend/scripts/fetch_bufdir_data.py
python3 backend/scripts/match_bufdir_robust.py
python3 backend/scripts/enrich_properties_bufdir.py
python3 backend/scripts/establish_bufdir_unmatched.py
```

Etter dette er både all nødvendig data og bildene lastet ned og brukt i systemet.

**For eiendommer som fortsatt mangler bilde** (f.eks. bufdir hadde ikke `image_url`): Kjør steg 5 for å søke på nettet:

```bash
./scripts/kjor_fetch_barnevern_images.sh
# Eller dry-run: ./scripts/kjor_fetch_barnevern_images.sh --dry-run
# Eller begrenset: ./scripts/kjor_fetch_barnevern_images.sh --limit 5
# Eller uten LLM (sparer API-kostnad): ./scripts/kjor_fetch_barnevern_images.sh --no-llm
```
