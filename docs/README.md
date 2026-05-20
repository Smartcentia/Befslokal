# docs/

**Start her:** [LOSNINGSOVERSIKT.md](LOSNINGSOVERSIKT.md) – samlet peker til arkitektur, KI Kollega, Bufdir, data og typiske feil.

---

Innhold som brukes av BEFS-appen:

| Fil | Brukes av |
|-----|------------|
| `BRUKERHJELP.md` | Brukerhjelp (HelpCenter) – parses av backend help_service. **Ved endring:** kjør `./scripts/sync_brukerhjelp.sh` for å synkronisere til backend/docs/ (Railway-deploy) |
| `technical.md` | Admin → Teknisk dokumentasjon |
| `RISK_OG_KOSTNADSANALYSE_METODIKK.md` | Metodikk for risikovurdering, kostnadsanalyse, budsjett og prioriteringsindeks |
| `CRON_INTERNKONTROLL.md` | Cron-jobs for internkontroll (process-due, process-overdue) |

## KI Kollega

| Fil | Beskrivelse |
|-----|-------------|
| **`KI_KOLLEGA_DATA_OG_FUNKSJON.md`** | **Samlet oversikt** – alle data KI Kollega har tilgang til, hvordan den fungerer, rollefiltrering, blokk |
| `KI_KOLLEGA_TEKNISK_GJENNOMGANG.md` | Full teknisk gjennomgang – arkitektur, kode, API, agenter, query_normalizer |
| `KI_KOLLEGA_HOW_IT_WORKS.md` | Hvordan flyten fungerer (brukerperspektiv) |
| `KI_KOLLEGA_TRE_MODUSER.md` | Enkel, Avansert, Fullverdig |
| `KI_KOLLEGA_EKSEMPELSPORSMAL.md` | Eksempelspørsmål (referanse) |
| `KI_KOLLEGA_FULLVERDIG_PLAN.md` | Full plan for Fullverdig modus – agenter, internkontroll, faser |

**Robust søk:** KI Kollega forstår forkortelser (fvk, BUP), synonymer (leietakere=parter) og vanlige skrivefeil. Se `BRUKERHJELP.md` og `befs_instruksjoner.txt`.

## Sikkerhet og teknisk

| Fil | Beskrivelse |
|-----|-------------|
| **`INFORMASJONSSIKKERHET.md`** | Informasjonssikkerhet – autentisering, roller, CORS, feilhåndtering, rate limiting |
| `SUPABASE_RAILWAY_TILKOBLING.md` | Hvorfor vi bruker pooler-URL og `+asyncpg` for Supabase fra Railway (IPv4, async driver) |
| [ENDPUNKT_SIKKERHET_ANALYSE.md](../dokumentasjon/ENDPUNKT_SIKKERHET_ANALYSE.md) | Detaljert endepunkt-sikkerhet – open paths, eksplisitt auth, rate limiting |

Øvrig dokumentasjon ligger i [../dokumentasjon/](../dokumentasjon/).
