# Eiendomsnavn fra registre og databaser

**Formål:** Oversikt over hvor eiendomsnavn finnes i BEFS sine datakilder, og hvordan de 65 eiendommer som kun har adresse som navn kan berikes.

---

## 1. Datakilder med eiendomsnavn

| Kilde | Fil/API | Felt | Format | Brukes av |
|-------|---------|------|--------|-----------|
| **Oversikt bygg og eiendom** | CSV (typisk ~/Downloads) | `Lokalisering` | `XXXX - Navn` (f.eks. `5107 - Familievernkontoret Innlandet øst - Tynset`) | `import_oversikt_bygg_eiendom_csv.py` |
| **e-don2 / e-dom** | `backend/e-don2.txt`, `e-dom.txt` | `Enhetsnavn` | Institusjons-/enhetsnavn | `import_edon2_data.py` → `DataManagementService.import_edon2_csv` |
| **Birk Institusjoner (ERA-01)** | CSV (f.eks. `Institusjoner i og utenfor staten - Formålsbygg...csv`) | `Enhetsnavn`, `Lokasjonskode`, `Adresse`, `Antall G/K - plasser`, `Eierskapenhet`, `Tilhørighet2` | Semikolon-separert, e-don2-kompatibel | Samme import: `import_edon2_csv` (støtter multi-source merge) |
| **Master data CSV** | Opplastet via API / import | `lokalisering` | `ID - Navn` | `DataManagementService.import_property_master_csv` |
| **Portfolio / Eiendomsportfeb** | CSV | `Lokalisering` | `ID - Navn` | `import_portfolio_2025.py` |
| **bufdir_matches_robust.json** | `backend/bufdir_matches_robust.json` | `property_name` | Eiendomsnavn for Bufdir-matcher | `match_bufdir_robust.py` |

---

## 2. Hva oppdaterer name i dag?

| Import | Oppdaterer `properties.name`? |
|--------|-------------------------------|
| **e-don2** | Ja – `prop.name = Enhetsnavn or prop.name` |
| **Master CSV** | Ja – `prop.name = lok_name` fra lokalisering |
| **Portfolio** | Ja – ved opprettelse og oppdatering |
| **Oversikt bygg** | **Nei** – bruker kun Lokalisering til matching, oppdaterer ikke name |

---

## 3. De 65 eiendommer med kun adresse

Disse har `name` som matcher adresseformat (f.eks. «Aumliveien 4C, 2500 Tynset»). Mange har `lokalisering_id` satt (f.eks. 5107, 5957) – da kan Oversikt bygg CSV brukes til å hente riktig navn.

**Eksempel:** Eiendom med `lokalisering_id=5107` og `name=Aumliveien 4C, 2500 Tynset` – Oversikt bygg CSV har rad «5107 - Familievernkontoret Innlandet øst - Tynset -Aumliveien 4C, 2500 Tynset» → navn «Familievernkontoret Innlandet øst - Tynset».

---

## 4. Berikingsscript

Scriptet `backend/scripts/berik_navn_fra_oversikt_bygg.py`:

1. Finner eiendommer med kun adresse som navn
2. Leser Oversikt bygg CSV
3. Matcher på `lokalisering_id` eller adresse
4. Oppdaterer `name` med navn fra CSV (kun når CSV-navnet er et egentlig eiendomsnavn, ikke bare adresse)

**Kjøring:**
```bash
cd backend
railway run python3 scripts/berik_navn_fra_oversikt_bygg.py [--csv PATH] [--dry-run]
```

Standard CSV-sti: `~/Downloads/Oversikt bygg og eiendom - GK og Budsjetterte(Ark1) (2).csv`

---

## 5. Familievernkontor-mapping

Manuell mapping fra Bufdir.no (adresse → navn) i `backend/data/familievernkontor_mapping.json`:

| Adresse | Navn |
|---------|------|
| Aumliveien 4C, 2500 Tynset | Familievernkontoret Innlandet Øst - Tynset |
| Vangsvegen 121, 2318 Hamar | Familievernkontoret Innlandet Øst - Hamar |
| Storgata 11, 3510 Hønefoss | Familievernkontoret Ringerike - Hallingdal, avdeling Ringerike |
| Kabelgata 2, 0581 Oslo | Familievernkontoret Oslo Nord |

**Kjør berikingsscript:**
```bash
cd backend && railway run python3 scripts/berik_navn_familievernkontor.py [--dry-run]
```

---

## 6. Eiendomsbilde

- **Bufdir-matchade eiendommer:** Bildet kommer fra `enrich_properties_bufdir.py` (cms.bufdir.no)
- **Andre eiendommer med koordinater:** `legg_til_eiendomsbilde.py` setter `external_data.mapbox_static` slik at frontend viser Mapbox static kart som fallback

**Kjør:**
```bash
cd backend && railway run python3 scripts/legg_til_eiendomsbilde.py [--dry-run]
```

Frontend viser eiendomsbilde øverst på eiendomssiden (Bufdir-foto eller Mapbox kart).

---

## 7. Birk Institusjoner CSV (ERA-01)

Birk Institusjoner CSV (barnevernsinstitusjoner i og utenfor staten) kan brukes som e-don2-kilde. Importen støtter multi-source merge – last opp både e-don2 og Birk CSV for å slå sammen data.

**Birk-spesifikke felt som importeres:**
- `Antall G/K - plasser` → `approved_places`
- `Eierskapenhet` → `ownership_type`
- `Tilhørighet2` → `external_data.birk_tilhorighet2`

---

## 8. Andre mulige kilder

- **birk_og_plasser.csv** (finans/) – har Enhetsnavn, brukes til mapping
- **Eiendomsportfeb** – Lokalisering med fullt navn
- **Eie1212** – eiendomslister med navn
