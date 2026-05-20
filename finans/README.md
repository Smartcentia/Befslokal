# Finans prediksjon (Excel)

Dette området inneholder skript og genererte Excel-filer for prediksjon.

## Årsregnskap (Agresso) vs. eiendomsøkonomi (BEFS)

| Perspektiv | Hva er «sannhet»? | Hva BEFS bruker |
|------------|-------------------|-----------------|
| **Juridisk / konsernregnskap** | Agresso (og tilhørende lønns-/personalprosesser) er bokførings- og rapporteringskilde mot årsregnskap og revisjon. | BEFS erstatter ikke Agresso. |
| **Portefølje og per eiendom** | Samme underliggende poster, men fordelt på **koststed (Dim1)** og andre dimensjoner. | **`gl_transactions`** (Agresso-eksport med bl.a. `property_id`) og **`salary_costs`** (lønnskost per år koblet til `property_id`). API/filtre kan regne eiendom som «aktiv» i et år om den har **GL eller lønn** for det året (se `backend/app/services/financials/source_coverage_service.py`). |

**Konsekvens:** Full dekningsgrad i BEFS (alle relevante Dim1 → eiendom, minimalt med ukoblede GL-rader) gir **god eiendomsøkonomisk oversikt**, men er **ikke** det samme som å verifisere hele årsregnskapet. Hull i `property_id` eller administrative koststed uten fysisk eiendom påvirker **analyse og SRS-rapporter**, ikke nødvendigvis korrekthet i Agresso.

**UI:** Sentraløkonomi (GL der `property_id` er tom, aggregert per koststed) — `/financials/sentral`, API `GET /api/v1/financials/gl-uten-eiendom?ar=YYYY`.

## Koststed (Dim1) → BEFS-eiendom

For **SRS** og sporbarhet i GL skal hver relevante Agresso-koststad (Dim1) være knyttet til en eiendom i BEFS via tabellen `koststed_mapping.property_id`.

**Arbeidsflyt (kort):**

1. **Masterliste** — CSV `finans/koststed_eiendom_mapping.csv` importeres til `koststed_mapping` (se `backend/scripts/import_koststed_mapping.py` eller admin-import).
2. **Automatisk kobling** — `POST /api/v1/admin/economic-import/link-koststed-properties` matcher `koststed_navn` mot `properties.name` (eksakt og delvis) og oppdaterer `gl_transactions.property_id` der koststedet er koblet.
3. **Kode-basert forslag** — kjør `backend/scripts/suggest_koststed_property_mapping.py` (dry-run) for å foreslå `property_id` på rader uten kobling, ved å sammenligne Dim1-kode med `properties.koststed_kode`, `unit_id_erp`, `department_code` og `lokalisering_id`. Valgfritt `--apply` for å skrive inn entydige treff.
4. **Oversikt i UI** — «SRS-samsvarrapport» (`/financials/srs`) viser dekningsgrad og en tabell over **ukoblede** koststed med GL-beløp per valgt år; **grønn** compliance for koststed krever **100 %** koblede rader.

**Merk:** Noen Dim1-koder kan være administrative eller uten fysisk eiendom; slike må avklares forretningsmessig før de mappes til en eiendom eller ekskluderes fra kravet.

## Generer lønnsprediksjon

```bash
python3 finans/lag_lonn_excel.py --pred-year 2026
python3 finans/lag_lonn_excel.py --pred-year 2027
python3 finans/lag_lonn_excel.py --pred-year 2028
```

Output:

- `finans/Prediksjon_<år>_Lønn.xlsx`

## Generer økonomiprediksjon

```bash
python3 finans/lag_prediksjon_excel.py --out-year 2026
python3 finans/lag_prediksjon_excel.py --out-year 2027
python3 finans/lag_prediksjon_excel.py --out-year 2028
```

Output:

- `finans/Prediksjon_<år>_Økonomi.xlsx`

**Metodikk (hvordan filen er utregnet):** se [METODE_Prediksjon_Økonomi.md](METODE_Prediksjon_Økonomi.md). I den genererte filen finnes arket **Antagelser** med globale vekstjusteringer som slår ut i prediksjonsark og forsiden.

## Merknad

- Midlertidige filer som starter med `~$` er Excel-låsefiler og kan ignoreres.
- Admin-side for nedlasting viser filer via API:
  - `GET /api/v1/barnevern-docs/prediction-excel`
