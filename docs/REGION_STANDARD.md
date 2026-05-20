# Regionstandard – BEFS

## Standardformat

Alle regioner og Bufdir bruker **kort format** i `properties.region` og `users.region`:

| Region / direktorat | Standardverdi | Alternativt navn |
|--------------------|----------------|-------------------|
| Region Nord | `Nord` | Region Nord |
| Region Midt | `Midt-Norge` | Region Midt-Norge |
| Region Vest | `Vest` | Region Vest |
| Region Sør | `Sør` | Region Sør |
| Region Øst | `Øst` | Region Øst |
| Bufdir (direktorat) | `Bufdir` | — |

**Bufdir er et eget direktorat** og mappes aldri til Øst eller andre regioner.

---

## Mapping fra andre formater

Ved import fra GL-filer, Excel, CSV osv. kan regioner komme som:

- `01 - Nord`, `02 - Midt-Norge`, `03 - Vest`, `04 - Sør`, `05 - Øst`, `06 - Bufdir`
- `Region Nord`, `Region Midt-Norge`, `Region Vest`, `Region Sør`, `Region Øst`
- `Region Midt` (= Midt-Norge)

Alle skal normaliseres til standardformatet over.

---

## Implementasjon

- **Sentral mapping:** `backend/app/domains/core/utils/region_mapping.py`
- **Import-normalisering:** `backend/app/scripts/import_master_data.py` → `normalize_region()`
- **Oppryddingsscript:** `backend/scripts/fix_regions.py`
