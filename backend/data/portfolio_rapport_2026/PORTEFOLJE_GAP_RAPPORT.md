# Portefølje og gap – prioritert rapport

_Generert: 2026-04-11 (kjøringer mot produksjonsdatabase via `railway run` der angitt)._

Denne rapporten knytter **anbefalt prioritering** for hele porteføljen til **faktiske tall** fra kjørte skript. Underliggende detaljfiler ligger i samme mappe: `backend/data/portfolio_rapport_2026/`.

## Kjørte skript

| Skript | Formål |
|--------|--------|
| `scripts/sync_bufdir_institutions.py` | Bufdir listing (alle eierformer), match mot `properties`, gap-filer |
| `scripts/audit_properties_quality_bufdir.py` | Datakvalitet, Bufdir-kobling i `external_data`, duplikater, regnskapskobling |
| `scripts/quick_stats.py` | Eiendommer, GL-dekning |
| `scripts/analyze_missing_properties.py` | Koststed uten property, navnematch mot GL |

**Ikke fullført:** `scripts/count_core_data.py` feilet ved første forsøk (feil system-Python / manglende modell-registrering). Kjeretall for eiendommer er hentet fra `quick_stats.py` og revisjonsrapporten (636 eiendommer).

**Supplement:** `supplementary_sitemap.json` er generert (finn-institusjon-detaljer og kontakt-relaterte URL-er fra sitemap).

---

## Kjeretall (oversikt)

| Mål | Verdi |
|-----|------:|
| Eiendommer (`properties`) | **636** |
| Bufdir-institusjoner i listing (alle eierformer) | **199** |
| Bufdir-rader med treff i BEFS (`match_property_id` satt) | **179** |
| Bufdir i offentlig register, **ikke** matchet til eiendom | **20** |
| Eiendommer **uten** noe Bufdir-listetreff | **584** |
| `property_id` som fikk **mer enn én** Bufdir-rad | **24** id-er (flere kort mot samme eiendom) |
| Eiendommer med minst ett kvalitetsavvik (revisjon) | **264** |
| Umappede koststed med GL-beløp | **278** |
| Aktive eiendommer uten budsjettprognose (2027 syntetisk) | **446** |
| Eiendommer med GL-transaksjoner | **190** (~29,9 %) |

---

## Prioritet 1 – Gjør først (høy effekt)

### 1A. Offentlig register vs BEFS (Bufdir)

**20** institusjoner fra Bufdir har **ingen** automatisk match i BEFS (`gap_not_in_befs.json`).  
Typiske årsaker: ekstern nettside uten besøksadresse i kortet, privat leverandør med annet navn enn hos dere, eller manglende eiendom i BEFS.

**Anbefaling:** Gå gjennom `gap_not_in_befs.json` først (liten mengde). Vurder manuell opprettelse eller alias/adresse-justering.

### 1B. Regnskap og koststed

Revisjonen viser **111** eiendommer uten `unit_id_erp` / `department_code` / `koststed_kode`.  
`analyze_missing_properties.py` viser **278** koststed med GL-data som **ikke** er koblet til `property_id`.

**Anbefaling:** Prioriter koststed med høyeste GL-volum (se skript-output). **52** navnebaserte forslag ble funnet (score ≥ 0,55) – krever faglig godkjenning (mange treff er «Regionkontor» / generiske navn).

### 1C. Duplikater og feil identitet

- **24** `property_id` hadde **flere** Bufdir-kort (`match_duplicate_property_ids.json`) – ofte flere avdelinger under samme juridiske adresse/leverandør.
- Revisjon: **93** tilfeller av **duplikatnavn** på tvers av eiendommer (`duplicate_property_name` i `properties_quality_audit.md`).

**Anbefaling:** Rydd duplikater og avklar «én rad vs flere lokasjoner» før bred attributtfylling.

---

## Prioritet 2 – Etter at nivå 1 er under kontroll

- **584** eiendommer i `gap_befs_not_in_bufdir.json`: **forventet stort tall** – Bufdir-listen dekker kun barnevernsinstitusjonsregisteret, ikke kontor, tomter, familievern osv. Filtrer på `unit_type_derived`, region eller «har kontrakt/koststed» før dere bruker tid på radene.
- **56** eiendommer har `bufdir_id` i data som **ikke** finnes i eksportert `bufdir_institutions.json` (ofte eldre id / endret register – se `bufdir_id_missing_in_json` i revisjonen).
- Geodata og adresse: **33** mangler geolokalisering, **11** mangler gateadresse, **29** navn ser ut som ren adresse.

---

## Prioritet 3 – Når basis er stabil

- Historikk, nedleggelser, full geokoding.
- Budsjett/prognose: **446** aktive uten prediction – egen arbeidskø (ikke det samme som Bufdir-gap).

---

## Vedlegg (filer)

| Fil | Innhold |
|-----|---------|
| `bufdir_institutions.json` / `.csv` | Full Bufdir-liste med match-felter |
| `gap_not_in_befs.json` | Bufdir uten BEFS-treff (**20**) |
| `gap_befs_not_in_bufdir.json` | BEFS uten Bufdir-treff (**584**) |
| `match_duplicate_property_ids.json` | Flere Bufdir → samme property (**24** id-er) |
| `../properties_quality_audit.md` | Full tabellrevisjon (kopiert `bufdir_institutions.json` til `backend/bufdir_institutions.json` før kjøring) |
| `_quick_stats.txt` | GL-statistikk |
| `_analyze_missing_properties.txt` | Koststed / prediction (kort utdrag) |

---

## Teknisk notat

- **Datakilde Bufdir:** HTML-listing `https://www.bufdir.no/barnevern/finn-institusjon/` (ingen stabilt offentlig JSON-API observert). Paginering: siste `?page=N` inneholder alle kort.
- **Matching:** `property_matcher` (adresse først, deretter navn fuzzy).
- **SQLAlchemy:** `sync_bufdir_institutions.py` er oppdatert med import av `center` / HMS-modeller slik at `Property`-mapping initialiseres korrekt under `railway run`.

Videre anbefaling: **be om maskinlesbar eksport fra Bufdir** for å redusere vedlikehold av HTML-parser; behold scraping som supplement til gap-analyse inntil det foreligger.
