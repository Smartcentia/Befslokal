# BEFS/KNOWME – løsningsoversikt

Kort navigasjon til **funksjonalitet**, **data** og **typiske feilkilder**. Detaljer ligger i lenkede dokumenter.

---

## 1. Hva løsningen gjør

| Område | Innhold | Les mer |
|--------|---------|---------|
| Arkitektur og kontekst | Containere, integrasjoner, sikkerhet, deploy | [ARKITEKTUR_BESKRIVELSE.md](ARKITEKTUR_BESKRIVELSE.md) |
| Kjerne domene | Eiendommer, enheter, kontrakter, parter | `backend/app/domains/core/routers/`, [frontend/lib/api/](../frontend/lib/api/) |
| Økonomi | Regnskap, kostnader, budsjett, prognoser, innkjøp | `backend/app/api/v1/financials.py`, `cost_management`, `costs`, `forecast` |
| HMS / risiko | Avvik, sjekklister, internkontroll, aktiviteter | `domains/hms/routers/` |
| KI | KI-Kollega, datakilder, rollefiltrering | [KI_KOLLEGA_DATA_OG_FUNKSJON.md](KI_KOLLEGA_DATA_OG_FUNKSJON.md) |
| Bufdir og institusjonsdata | Nedlasting, matching, berikelse, revisjonsskript | [BUFDIR_PIPELINE.md](BUFDIR_PIPELINE.md) |
| Begreper og region | Bufetat vs Bufdir, regionstandard | [BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md](BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md), [REGION_STANDARD.md](REGION_STANDARD.md) |
| Sikkerhet | Auth, roller, CORS | [INFORMASJONSSIKKERHET.md](INFORMASJONSSIKKERHET.md) |
| Frontend API-lag | Moduler og mønster | [../.cursor/rules/api-structure.mdc](../.cursor/rules/api-structure.mdc) |

**Målgruppe:** Eiendomsforvaltning for Bufetat – ikke personsensitive barnevernssaker som kjerne, men eiendom, kontrakter, økonomi, HMS og beslutningsstøtte.

---

## 2. Data (kort)

- **Database:** PostgreSQL (+ pgvector der relevant). Kjerneentitet `properties` med bl.a. `external_data` (JSONB) for Bufdir, finans m.m. – se [backend/app/domains/core/models/property.py](../backend/app/domains/core/models/property.py).
- **Autentisering:** Supabase-sesjon + backend med delt hemmelighet og `X-User-Email` – se [CLAUDE.md](../CLAUDE.md).
- **Bufdir-fil:** `backend/bufdir_institutions.json` (etter `fetch_bufdir_data.py`); kvalitetsrevisjon: `backend/scripts/audit_properties_quality_bufdir.py`.

---

## 3. Typiske feil og blindsoner

| Tema | Risiko |
|------|--------|
| Deploy | Feil Railway-prosjekt eller feil `DATABASE_URL` – se [DEPLOY_SJEKKLISTE.md](DEPLOY_SJEKKLISTE.md) (Railway-prosjekter). |
| Miljø | `load_dotenv(override=True)` i skript kan overskrive `railway run`; preferer `override=False` når miljø allerede er satt. |
| Frontend | `NEXT_PUBLIC_API_URL` er **bakt inn ved build** – må stemme med produksjons-backend. |
| RBAC | Feil tilgangsfilter kan gi for mye eller for lite data. |
| Datakvalitet | Navn vs adresse, utdatert Bufdir-JSON, flere kilder (e-don2 vs Bufdir) – se [BUFDIR_PIPELINE.md](BUFDIR_PIPELINE.md). |
| KI | Hallusinasjon / feil verktøy – begrenses av instruksjoner, elimineres ikke fullt ut. |

---

## 4. Indeks: øvrig dokumentasjon

Se [README.md](README.md) for full tabell over `docs/`-filer (brukerhjelp, KI-detaljer, cron, osv.).

---

## 5. Alt på ett sted: datarevisjon og finans

| Hva | Hvor / kommando |
|-----|------------------|
| Begreper (kontrakt vs GL vs manuelt) | [DATAKILDER_EIENDOM_FINANS.md](DATAKILDER_EIENDOM_FINANS.md) |
| Bufdir, adresse, geodata, koblingsnøkler | `cd backend && PYTHONPATH=. .venv/bin/python scripts/audit_properties_quality_bufdir.py` → `backend/data/properties_quality_audit.md` |
| Helhetlig kompletthet (enheter, kontrakt, GL, score, CSV) | `cd backend && PYTHONPATH=. .venv/bin/python scripts/audit_properties_full.py` → `backend/data/property_completeness_audit.csv` og `.md` |
| Begge revisjonsskript i én forgrunnskjøring | `backend/scripts/run_all_property_audits.sh` – lokalt: `cd backend && ./scripts/run_all_property_audits.sh`; med Railway: `railway run bash backend/scripts/run_all_property_audits.sh` (fra repo-rot) |
| Produksjons-DB med Railway (ett skript) | `railway run bash -c 'cd backend && PYTHONPATH=. .venv/bin/python scripts/audit_properties_full.py'` (fra repo-rot) |
| Admin UI | **Finansiell analyse** – detaljer viser «Datakilder (to lag)» + score |
| API (admin) | `GET /api/v1/admin/financial-analysis/completeness-summary`, `GET .../completeness/{property_id}`; detalj på eiendom utvides med `data_sources` på `GET .../financial-analysis/property/{id}` |

**Etter revisjon:** prioriter `missing_accounting_linkage`, deretter `no_gl_in_window` / `double_hole_no_finance`, deretter kontraktsbeløp og avvikene `anomaly_*` der det er relevant for forretningen.
