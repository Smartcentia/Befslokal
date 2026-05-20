# Fellesbyg og Dim2-adresse-matching

## Problem

For fellesbyg som **Tærudgata 16 (Portalen)** i Lillestrøm bruker mange avdelinger samme bygg. I GL-data har transaksjoner ofte `Dim2(T)` = adresse (f.eks. "Tærudgata 16, 2004 Lillestrøm").

**Feil:** CSV-import (data_management) brukte Dim2-adresse til å matche transaksjoner mot eiendom. Da ble alle kostnader fra alle avdelinger som bruker bygget, aggregert til én eiendom – med feil budsjettavvik (f.eks. −891 %).

**Riktig:** Kostnaden tilhører **avdelingen** (Dim1/koststed), ikke eiendommen. Eiendom skal matches via `unit_id_erp` = Dim1, ikke via Dim2-adresse.

## Løsning

### 1. Svarteliste i import

`backend/app/services/data_management.py` har nå `FELLESBYGG_ADDRESSES`. PASS 2 (adresse-matching på Dim2) **hoppes over** når Dim2 matcher en fellesbyg-adresse.

### 2. Orphan-script

`backend/scripts/analyse_orphan_address_matches.py` ekskluderer fellesbyg fra adresse-matching. `--apply` vil aldri sette `property_id` til Tærudgata 16 basert på Dim2/supplier.

### 3. Rette eksisterende data

Kjør scriptet for å nullstille feilaktig matchede transaksjoner:

```bash
cd backend
railway run python scripts/fix_fellesbyg_property_mismatch.py --dry-run  # Først sjekk
railway run python scripts/fix_fellesbyg_property_mismatch.py            # Kjør
```

Scriptet nullstiller `property_id` på transaksjoner som:
- er tilknyttet en fellesbyg-eiendom (adresse i svartelisten)
- og har `department_code` ≠ `property.unit_id_erp` (dvs. matchet via adresse, ikke koststed)

## Legge til flere fellesbyg

Utvid `FELLESBYGG_ADDRESSES` i:
- `backend/app/services/data_management.py`
- `backend/scripts/analyse_orphan_address_matches.py`
- `backend/scripts/fix_fellesbyg_property_mismatch.py`

Format: lowercase, med og uten postnummer/poststed (f.eks. "tærudgata 16", "tærudgata 16, 2004 lillestrøm").
