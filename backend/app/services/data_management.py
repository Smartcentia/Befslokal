
import pandas as pd
import io
import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, text
from datetime import datetime
import re
import math
import difflib
import csv

from app.models.financial_models import Budget, GLTransaction
from app.models.text_content import TextContent
from app.models.socioeconomic import SocioeconomicData
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.utils.csv_source_mapping import OK1_GL_SCHEMA, EIENDOM_GL_SCHEMA

logger = logging.getLogger(__name__)

# Column mapping – bruk sentral csv_source_mapping
_OK1_MAPPING = OK1_GL_SCHEMA
_EIENDOM_MAPPING = EIENDOM_GL_SCHEMA


def _parse_beloep(val) -> Optional[float]:
    """Parse Norwegian Visma amount: '1,234.56' or '(1,234.56)' for negatives."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    negative = s.startswith('(') and s.endswith(')')
    s = s.replace('(', '').replace(')', '').replace(',', '')
    try:
        result = float(s)
        return -result if negative else result
    except ValueError:
        return None


def _parse_ok1_amount(val) -> Optional[float]:
    """Parse ok1.csv amount: comma as decimal separator, space as thousands."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, str):
        return float(val.replace(',', '.').replace(' ', ''))
    return float(val)


_ID_MISSING = {"", "nan", "none", "null"}

# Adresser for fellesbyg hvor Dim2 = adresse IKKE skal brukes til property-matching.
# Mange koststeder deler samme bygg; kostnaden tilhører avdelingen, ikke eiendommen.
FELLESBYGG_ADDRESSES = frozenset({
    "tærudgata 16",
    "tærudgata 16, 2004 lillestrøm",
    "tærudgata 16 2004 lillestrøm",
})


def _is_fellesbyg_address(dim2_val: Any) -> bool:
    """Sjekk om Dim2(T)-verdi er en kjent fellesbyg-adresse (ikke bruk for matching)."""
    if not dim2_val or (isinstance(dim2_val, float) and pd.isna(dim2_val)):
        return False
    s = str(dim2_val).strip().lower()
    if not s:
        return False
    clean = s.split(",")[0].strip()
    return clean in FELLESBYGG_ADDRESSES or s in FELLESBYGG_ADDRESSES


def _normalize_id(val: Any) -> Optional[str]:
    """Normalize ERP/EnhetID-like codes (Dim1, unit_id_erp). Same logic as e-don2 import."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s or s.lower() in _ID_MISSING:
        return None
    s = s.replace("\u00A0", " ").strip()
    if re.fullmatch(r"[-+]?\d+\.0", s):
        s = s.rsplit(".0", 1)[0]
    if re.fullmatch(r"\d+", s):
        return s
    return s

class DataManagementService:
    @staticmethod
    async def clear_all_economic_data(db: AsyncSession) -> Dict[str, Any]:
        """
        Clears ALL financial/economic data – transaksjonstabell, budsjett,
        JSONB-finansdata på eiendommer og kontrakter, prognoser og vedlikeholdskostnader.
        Berører IKKE eiendommer, kontrakter eller leietakere som stamdata.
        """
        try:
            # 1. Transaksjons- og budsjett-tabeller
            await db.execute(delete(GLTransaction))
            await db.execute(delete(Budget))
            await db.execute(delete(TextContent))
            await db.execute(delete(SocioeconomicData))

            # 2. Prognoser og scenarioer (avledede/cachede data)
            await db.execute(text("DELETE FROM forecast_cache"))
            await db.execute(text("DELETE FROM scenarios"))

            # 3. Vedlikeholdskostnader på bygningskomponenter
            await db.execute(text("UPDATE maintenance_records SET cost = NULL WHERE cost IS NOT NULL"))

            # 4. Finansiell JSONB på eiendommer – fjern hele 'financials'-nøkkelen
            await db.execute(
                text("""
                    UPDATE properties
                    SET external_data = external_data - 'financials'
                    WHERE external_data ? 'financials'
                """)
            )

            # 5. Finansielle JSONB-felt på kontrakter
            await db.execute(
                text("""
                    UPDATE contracts
                    SET external_data = external_data
                        - 'common_costs'
                        - 'internal_maintenance_cost'
                        - 'municipal_fees'
                        - 'energy_cost'
                        - 'heating_cost'
                    WHERE external_data IS NOT NULL
                """)
            )

            # 6. Direkte kostnadskolonner på kontrakter
            await db.execute(
                text("""
                    UPDATE contracts
                    SET caretaker_cost = NULL,
                        cleaning_cost = NULL,
                        parking_cost = NULL,
                        card_reader_cost = NULL
                """)
            )

            await db.commit()
            return {
                "status": "success",
                "message": "All economic data cleared: gl_transactions, budget, text_content, "
                           "forecast_cache, scenarios, maintenance costs, "
                           "property financials JSONB, contract cost fields."
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error clearing data: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def import_financial_csv(db: AsyncSession, file_content: bytes) -> Dict[str, Any]:
        """
        Imports financial data from CSV into GLTransaction.
        Auto-detects format: ok1.csv (Xledger legacy) or Eiendomfebruar.csv (new Visma).
        """
        try:
            # Detect encoding (norske regnskapsfiler er ofte Windows-1252)
            encoding = 'utf-8'
            content_sample = ''
            for enc in ('utf-8-sig', 'windows-1252', 'latin-1', 'utf-8'):
                try:
                    content_sample = file_content[:1000].decode(enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            delimiter = ';' if ';' in content_sample else ','

            df = pd.read_csv(
                io.BytesIO(file_content),
                sep=delimiter,
                encoding=encoding,
                dtype=str,      # keep everything as string to avoid type surprises
            )
            df.columns = df.columns.str.strip()

            # Auto-detect format by column presence
            is_eiendom_format = 'Dim1' in df.columns
            mapping = _EIENDOM_MAPPING if is_eiendom_format else _OK1_MAPPING
            logger.info(f"CSV format detected: {'Eiendomfebruar/Visma' if is_eiendom_format else 'ok1/Xledger'}")

            # Build Dim1 → Dim2(T) fallback for rows where Dim2(T) is missing.
            # Only use Dim1 codes that CONSISTENTLY map to exactly ONE Dim2(T) address.
            dim1_fallback: Dict[str, str] = {}
            if is_eiendom_format and 'Dim1' in df.columns and 'Dim2(T)' in df.columns:
                from collections import defaultdict
                dim1_dim2_sets: Dict[str, set] = defaultdict(set)
                for _, r in df.iterrows():
                    d1 = str(r.get('Dim1', '') or '').strip()
                    d2 = str(r.get('Dim2(T)', '') or '').strip()
                    if d1 and d2:
                        dim1_dim2_sets[d1].add(d2)
                dim1_fallback = {k: list(v)[0] for k, v in dim1_dim2_sets.items() if len(v) == 1}
                logger.info(f"Dim1 fallback mapping: {len(dim1_fallback)} consistent 1:1 entries")

            imported_count = 0
            errors = 0

            # Pre-fetch properties and addresses for normalization
            result = await db.execute(select(Property))
            properties = result.scalars().all()
            
            # Helper for address normalization
            def normalize_addr(s: str) -> str:
                if not s: return ""
                s = s.lower()
                # Remove common noise and standardize
                s = re.sub(r'\d+', '', s) # Remove numbers
                s = s.replace('gt.', 'gate').replace('veien', 'vn').replace('gate', 'gt') # standard suffixes
                return re.sub(r'[^a-zA-ZæøåÆØÅ]', '', s).strip() # letters only

            prop_lookup: Dict[str, Any] = {}
            norm_prop_lookup: Dict[str, Any] = {}
            for p in properties:
                if p.name:
                    prop_lookup[p.name.lower()] = p.property_id
                if p.address:
                    addr = p.address.lower()
                    prop_lookup[addr] = p.property_id
                    norm_prop_lookup[normalize_addr(addr)] = p.property_id

            # Dim1 (department_code) = EnhetID = property.unit_id_erp – direct lookup (PASS 0)
            unit_id_erp_to_property: Dict[str, uuid.UUID] = {}
            for p in properties:
                n = _normalize_id(p.unit_id_erp)
                if n:
                    if n in unit_id_erp_to_property and unit_id_erp_to_property[n] != p.property_id:
                        logger.warning(f"Duplicate unit_id_erp {n!r} for properties {unit_id_erp_to_property[n]}, {p.property_id}; first wins")
                    else:
                        unit_id_erp_to_property.setdefault(n, p.property_id)
            props_with_erp = len(unit_id_erp_to_property)
            logger.info(f"GL import: {props_with_erp} properties with unit_id_erp for Dim1 lookup")

            # Cache for learned mappings: DeptCode -> PropertyID
            learned_mappings: Dict[str, uuid.UUID] = {}
            invoice_to_prop: Dict[str, uuid.UUID] = {} # For rebooking propagation
            pass0_matches = 0  # Matches via Dim1 → unit_id_erp

            batch_size = 1000
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                transactions = []

                for _, row in batch_df.iterrows():
                    try:
                        data: Dict[str, Any] = {}
                        for csv_col, model_col in mapping.items():
                            raw = row.get(csv_col)
                            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                                raw = None
                            elif isinstance(raw, str) and raw.strip() == '':
                                raw = None
                            data[model_col] = raw

                        # --- Amount parsing ---
                        if is_eiendom_format:
                            data['amount'] = _parse_beloep(data.get('amount'))
                        else:
                            raw_amt = data.get('amount')
                            data['amount'] = _parse_ok1_amount(raw_amt) if raw_amt else None

                        # --- Date/Period parsing ---
                        raw_date = data.pop('_transaction_date_raw', None)
                        if raw_date:
                            try:
                                data['transaction_date'] = datetime.strptime(str(raw_date).strip(), '%m/%d/%Y')
                            except ValueError:
                                data['transaction_date'] = None

                        raw_year = data.pop('_year_raw', None)
                        period = data.get('period')
                        if raw_year:
                            try: data['year'] = int(str(raw_year).strip())
                            except ValueError: pass
                        if period and len(str(period).strip()) == 6:
                            s_period = str(period).strip()
                            if 'year' not in data or data.get('year') is None:
                                data['year'] = int(s_period[:4])
                            data['month'] = int(s_period[4:])

                        # --- Property Matching (Multi-Pass Heuristics) ---
                        dept_code = data.get('department_code')
                        dim2_t = data.get('dim2_name')
                        ba = data.get('ba_code')
                        inv_nr = data.get('invoice_number')
                        prop_id = None

                        # PASS 0: Dim1 (koststed) = EnhetID = property.unit_id_erp – most reliable link
                        norm_dept = _normalize_id(dept_code) if dept_code else None
                        if dept_code and norm_dept and norm_dept in unit_id_erp_to_property:
                            prop_id = unit_id_erp_to_property[norm_dept]
                            learned_mappings[dept_code] = prop_id
                            learned_mappings[norm_dept] = prop_id  # så PASS 1 treffer for "1234" og "1234.0"
                            pass0_matches += 1

                        # PASS 1: Learned Mapping (Direct Link, inkl. normalisert Dim1 fra PASS 0)
                        if not prop_id and (dept_code in learned_mappings or (norm_dept and norm_dept in learned_mappings)):
                            prop_id = learned_mappings.get(dept_code) or (norm_dept and learned_mappings.get(norm_dept))

                        # PASS 2: Address Matching (Exact or Fuzzy)
                        # Skip for fellesbyg – Dim2 = adresse betyr ikke at kostnaden tilhører eiendommen
                        if not prop_id and dim2_t and not _is_fellesbyg_address(dim2_t):
                            clean_name = str(dim2_t).split(',')[0].strip().lower()
                            # 2a. Direct string check
                            prop_id = prop_lookup.get(clean_name)
                            if not prop_id:
                                # 2b. Normalized check
                                norm_tx = normalize_addr(clean_name)
                                prop_id = norm_prop_lookup.get(norm_tx)
                            
                            if not prop_id:
                                # 2c. Fuzzy Match (high threshold)
                                from fuzzywuzzy import fuzz
                                best_score = 0
                                for m_addr, m_id in norm_prop_lookup.items():
                                    score = fuzz.ratio(norm_tx, m_addr)
                                    if score > 85 and score > best_score:
                                        best_score = score
                                        prop_id = m_id
                            
                            # If matched, learn it (begge nøkler så PASS 1 treffer uavhengig av Dim1-format)
                            if prop_id and dept_code:
                                learned_mappings[dept_code] = prop_id
                                if norm_dept:
                                    learned_mappings[norm_dept] = prop_id

                        # PASS 3: Rebooking Propagation (H1, H2, HB)
                        if not prop_id and ba in ['H1', 'H2', 'HB'] and inv_nr:
                            prop_id = invoice_to_prop.get(inv_nr)

                        # PASS 4: Legacy Fallbacks (Dim1 fallback / Dept Name)
                        if not prop_id and dim1_fallback:
                            fallback_addr = dim1_fallback.get(dept_code)
                            if fallback_addr:
                                prop_id = prop_lookup.get(fallback_addr.lower())

                        if not prop_id and data.get('department_name'):
                            dept_name = str(data['department_name']).strip().lower()
                            prop_id = prop_lookup.get(dept_name)

                        # Store successful links for rebooking passes
                        if prop_id and inv_nr:
                            invoice_to_prop[inv_nr] = prop_id

                        if not prop_id:
                            errors += 1
                            continue

                        data['property_id'] = prop_id
                        data['transaction_id'] = uuid.uuid4()
                        data['created_at'] = datetime.utcnow()
                        data['data_source'] = "CSV Import (Heuristic)"

                        # Remove keys not in model
                        valid_cols = {c.key for c in GLTransaction.__table__.columns}
                        data = {k: v for k, v in data.items() if k in valid_cols}

                        transactions.append(GLTransaction(**data))
                        imported_count += 1

                    except Exception as row_err:
                        logger.error(f"Error processing row: {row_err}")
                        errors += 1

                if transactions:
                    db.add_all(transactions)
                    await db.flush()

            logger.info(f"GL import: {pass0_matches} rows matched via Dim1 → unit_id_erp (PASS 0)")
            await db.commit()
            return {
                "status": "success",
                "imported": imported_count,
                "errors": errors,
                "total_rows": len(df),
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Import failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def import_property_master_csv(db: AsyncSession, file_content: bytes) -> Dict[str, Any]:
        """
        Imports or updates property and contract master data from totalny.txt / Eie1212 format.
        """
        try:
            content_sample = file_content[:2000].decode('utf-8-sig', errors='ignore')
            delimiter = '\t' if '\t' in content_sample else (';' if ';' in content_sample else ',')
            
            df = pd.read_csv(
                io.BytesIO(file_content),
                sep=delimiter,
                encoding='utf-8-sig',
                dtype=str
            )
            df.columns = df.columns.str.strip().str.lower()
            
            imported_props = 0
            updated_props = 0
            
            # Fetch existing records
            res = await db.execute(select(Property))
            existing_properties = {p.address.lower() if p.address else f"none-{p.property_id}": p for p in res.scalars().all()}
            
            def _str(val):
                """Convert pandas value to str or None, handling NaN."""
                if val is None:
                    return None
                import math
                try:
                    if isinstance(val, float) and math.isnan(val):
                        return None
                except Exception:
                    pass
                s = str(val).strip()
                return s if s and s.lower() != 'nan' else None

            for _, row in df.iterrows():
                # Extract ID and Name from Lokalisering if possible
                loc = _str(row.get('lokalisering')) or ''
                lok_id, lok_name = None, loc
                if " - " in loc:
                    parts = loc.split(" - ", 1)
                    lok_id = parts[0].strip()
                    lok_name = parts[1].strip()

                addr = _str(row.get('adresselinje 1'))
                if not addr: continue

                prop = existing_properties.get(addr.lower())
                is_new = False
                if not prop:
                    prop = Property(property_id=uuid.uuid4(), address=addr)
                    db.add(prop)
                    is_new = True

                prop.lokalisering_id = lok_id
                prop.name = lok_name
                prop.usage = _str(row.get('type lokasjon'))
                prop.municipality = _str(row.get('kommunenavn'))
                region_raw = _str(row.get('lok: distrikt')) or ''
                prop.region = region_raw.split(' - ', 1)[1].strip() if ' - ' in region_raw else (region_raw or None)
                
                try:
                    area_raw = str(row.get('areal', '0')).replace(',', '.')
                    prop.total_area = float(re.sub(r'[^\d.]', '', area_raw))
                except: pass
                
                # External data merge
                if not prop.external_data: prop.external_data = {}
                ext = prop.external_data.copy()
                ext['master_import_date'] = datetime.utcnow().isoformat()
                ext['raw_lokalisering'] = loc
                prop.external_data = ext
                
                if is_new: imported_props += 1
                else: updated_props += 1

            await db.commit()
            return {"status": "success", "imported": imported_props, "updated": updated_props}
        except Exception as e:
            await db.rollback()
            logger.error(f"Master import failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def import_edon2_csv(db: AsyncSession, file_contents: Union[bytes, List[bytes]], filename: str = "import") -> Dict[str, Any]:
        """
        Imports or updates property data from e-don2.txt format with tiered matching (v2.1).
        Supports multi-source merging by accepting a list of file contents.
        """
        try:
            # 0. Load Data - Support single or multiple files
            if isinstance(file_contents, bytes):
                file_contents = [file_contents]
            
            all_dfs = []
            alt_names = {
                'lokasjon/id': 'Lokasjonskode',
                'eiendomsid': 'Lokasjonskode',
                'enhet': 'EnhetID',
                'erp-id': 'EnhetID',
                'enhet-id': 'EnhetID',
                'erpid': 'EnhetID',
                'enhetsnavn': 'Enhetsnavn',
                'enhetnavn': 'Enhetsnavn',
                'enhetskorttype': 'Enhetskorttype',
                'enhetstype (utledet)': 'Enhetstype (Utledet)',
                'adresse': 'Adresse',
                'adresselinje 1': 'Adresse',
                # Birk Institusjoner CSV (ERA-01)
                'antall g/k - plasser': 'Antall_GK_plasser',
                'antall budsjetterte plasser': 'Antall_budsjetterte_plasser',
                'eierskapenhet': 'Eierskapenhet',
                'hjemler': 'Hjemler',
                'tilhørighet2': 'Tilhorighet2',
            }
            
            for i, content in enumerate(file_contents):
                if not content: continue
                sample = content[:2000].decode('utf-8', errors='ignore')
                delim = '\t' if '\t' in sample else (';' if ';' in sample else ',')
                
                curr_df = pd.read_csv(io.BytesIO(content), sep=delim, encoding='utf-8', dtype=str, on_bad_lines='skip')
                curr_df.columns = curr_df.columns.str.strip()
                
                # Normalize columns for this specific DF before merging
                curr_df.rename(columns=lambda x: alt_names.get(x.lower(), x), inplace=True)
                
                # Ensure we don't have duplicate normalized column names in this DF
                curr_df = curr_df.loc[:, ~curr_df.columns.duplicated()]
                
                print(f"DEBUG File {i}: Found columns: {list(curr_df.columns)}")
                if 'Lokasjonskode' in curr_df.columns:
                    sample_loks = curr_df['Lokasjonskode'].dropna().unique()[:5]
                    print(f"  - Sample Lokasjonskoder: {list(sample_loks)}")
                
                all_dfs.append(curr_df)
            
            if not all_dfs:
                return {"status": "error", "message": "No data found in provided files."}
            
            # Merge DataFrames (aligning columns)
            df = pd.concat(all_dfs, ignore_index=True)
            print(f"DEBUG: Merged DataFrame has {len(df)} rows and {len(df.columns)} columns.")
            
            # Ensure required columns
            required = ['Lokasjonskode', 'EnhetID', 'Enhetsnavn', 'Adresse']
            for col in required:
                if col not in df.columns:
                    # Look for case-insensitive matches
                    matches = [c for c in df.columns if c.lower() == col.lower()]
                    if matches:
                        df.rename(columns={matches[0]: col}, inplace=True)
                    else:
                        # Create empty column if missing to avoid failure
                        df[col] = None

            # Deduplicate - Keep row with most non-null data for each EnhetID
            if 'EnhetID' in df.columns:
                df['non_null_count'] = df.apply(lambda r: r.count(), axis=1)
                df = df.sort_values('non_null_count', ascending=False).drop_duplicates('EnhetID').drop(columns='non_null_count')
            
            # 1. Helper Normalization Functions
            _MISSING_IDS = {"", "nan", "none", "null"}
            def _normalize_id(val):
                if val is None: return None
                s = str(val).strip()
                if not s or s.lower() in _MISSING_IDS: return None
                
                # Normalize whitespace
                s = s.replace("\u00A0", " ").strip()
                
                # Remove .0 suffix if it's a whole number
                if re.fullmatch(r"[-+]?\d+\.0", s):
                    return s.rsplit('.0', 1)[0]
                
                # If pure digits, return as is
                if re.fullmatch(r"\d+", s):
                    return s
                
                return s

            def _normalize_address_canonical(val):
                if val is None: return ""
                s = str(val).strip().lower()
                s = re.sub(r'[\s\t\r\n]+', ' ', s) # Normalize whitespace
                s = re.sub(r'[.,;:-]', '', s) # Strip punctuation
                return s.strip()

            def _normalize_address_heuristic(val):
                """Suffix equivalence for lookup key only"""
                s = _normalize_address_canonical(val)
                # Heuristic equivalences: gata/gaten, veien/vegen
                s = s.replace('gata', 'gt').replace('gaten', 'gt')
                s = s.replace('veien', 'vg').replace('vegen', 'vg')
                return s

            # 2. Preparation: Index Existing Properties
            res = await db.execute(select(Property))
            all_props = res.scalars().all()
            
            by_lok_id = {}
            by_unit_id_erp = {}
            by_address_norm = {}
            by_address_heuristic = {} # list for potential collisions
            
            for p in all_props:
                lk = _normalize_id(p.lokalisering_id)
                if lk: by_lok_id[lk] = p
                
                ue = _normalize_id(p.unit_id_erp)
                if ue: by_unit_id_erp[ue] = p
                
                addr_can = _normalize_address_canonical(p.address)
                if addr_can: by_address_norm[addr_can] = p
                
                addr_heur = _normalize_address_heuristic(p.address)
                if addr_heur:
                    if addr_heur not in by_address_heuristic:
                        by_address_heuristic[addr_heur] = []
                    by_address_heuristic[addr_heur].append(p)

            TARGET_LOKS = ["1217", "2335", "3608", "3522", "5107", "5957", "1214", "4717", "2408", "2315", "4807", "3560", "2403"]
            print(f"DEBUG: Index check for targets in DB by_lok_id: {[t for t in TARGET_LOKS if t in by_lok_id]}")
            print(f"DEBUG: Index Sample - by_unit_id_erp keys: {list(by_unit_id_erp.keys())[:20]}")

            # 3. Processing and Tiered Matching
            proposed_matches = [] # list of (row_data, property_obj, method, score)
            in_flight_erp_ids = {} # unit_id_erp -> property_id
            errors = []
            
            for index, row in df.iterrows():
                row_raw_lok = row.get('Lokasjonskode')
                row_raw_unit = row.get('EnhetID')
                row_lok = _normalize_id(row_raw_lok)
                row_unit = _normalize_id(row_raw_unit)
                
                if index < 10 or row_lok in TARGET_LOKS:
                    print(f"DEBUG Row {index}: RAW lok='{row_raw_lok}' -> parsed='{row_lok}', RAW unit='{row_raw_unit}' -> parsed='{row_unit}', Name='{row.get('Enhetsnavn')}'")

                row_addr = row.get('Adresse')
                row_can = _normalize_address_canonical(row_addr)
                row_heur = _normalize_address_heuristic(row_addr)
                row_muni = str(row.get('Kommune') or "").strip().lower()
                row_reg = str(row.get('Region') or "").strip().lower()

                prop = None
                method = None
                score = 1.0

                # Tier 1: Exact Match (ID or Address)
                if row_lok and row_lok in by_lok_id:
                    prop = by_lok_id[row_lok]
                    method = "exact_lokalisering_id"
                elif row_unit and row_unit in by_unit_id_erp:
                    prop = by_unit_id_erp[row_unit]
                    method = "exact_unit_id_erp"
                elif row_can and row_can in by_address_norm:
                    prop = by_address_norm[row_can]
                    method = "exact_address"
                
                if (index < 10 or row_lok in TARGET_LOKS) and prop:
                    print(f"  - MATCHED via {method}: {prop.name} ({prop.property_id})")
                elif (index < 10 or row_lok in TARGET_LOKS):
                    print(f"  - NO MATCH for {row_lok or row_unit}. Source Address: '{row_addr}'")
                
                # Tier 2: Heuristic Match (Suffix equivalence)
                if not prop and row_heur and row_heur in by_address_heuristic:
                    candidates = by_address_heuristic[row_heur]
                    if len(candidates) == 1:
                        prop = candidates[0]
                        method = "heuristic_address"
                    else:
                        # Ambiguous heuristic match - skip auto-link
                        pass

                # Tier 3: Guarded Fuzzy Match
                if not prop and row_can:
                    # Filter candidates by Municipality/Region
                    # Relaxed: Allow empty municipality/region in DB as potential matches
                    potentials = [p for p in all_props if 
                                  (not row_muni or not p.municipality or str(p.municipality or "").strip().lower() == row_muni or 
                                   not row_reg or not p.region or str(p.region or "").strip().lower() == row_reg)]
                    
                    best_match = None
                    best_score = 0.0
                    second_best_score = 0.0
                    
                    for p in potentials:
                        p_can = _normalize_address_canonical(p.address)
                        if not p_can: continue
                        
                        s = difflib.SequenceMatcher(None, row_can, p_can).ratio()
                        if s > best_score:
                            second_best_score = best_score
                            best_score = s
                            best_match = p
                        elif s > second_best_score:
                            second_best_score = s
                    
                    # Thresholds: Score >= 0.85, Margin >= 0.05
                    if best_match and best_score >= 0.85 and (best_score - second_best_score >= 0.05):
                        prop = best_match
                        method = "fuzzy_address"
                        score = round(best_score, 4)
                        
                # Tier 4: Fuzzy Name Match (if address match failed or was weak)
                if not prop:
                    row_name = str(row.get('Enhetsnavn') or "").strip().lower()
                    if row_name and len(row_name) > 5:
                        best_match = None
                        best_score = 0.0
                        for p in all_props:
                            p_name = str(p.name or "").strip().lower()
                            if not p_name: continue
                            s = difflib.SequenceMatcher(None, row_name, p_name).ratio()
                            if s > best_score:
                                best_score = s
                                best_match = p
                        
                        if best_match and best_score >= 0.90:
                            prop = best_match
                            method = "fuzzy_name"
                            score = round(best_score, 4)

                if prop:
                    # Multi-level Duplicate Check (In-flight and DB)
                    if row_unit:
                        # 1. In-flight check
                        if row_unit in in_flight_erp_ids and in_flight_erp_ids[row_unit] != prop.property_id:
                            errors.append(f"Hard Stop: Duplicate ERP ID '{row_unit}' proposed for different properties in this run (Row {index}).")
                        # 2. Database check
                        existing_p = by_unit_id_erp.get(row_unit)
                        if existing_p and existing_p.property_id != prop.property_id:
                            errors.append(f"Hard Stop: ERP ID '{row_unit}' already assigned to Property '{existing_p.name}' ({existing_p.property_id}) in DB (Row {index}).")
                        
                        in_flight_erp_ids[row_unit] = prop.property_id
                    
                    proposed_matches.append({
                        'row': row,
                        'prop': prop,
                        'method': method,
                        'score': score
                    })

            if errors:
                return {"status": "error", "message": "Validation failed", "errors": errors[:10]}

            # 4. Final Updates and Audit Log
            audit_data = []
            updated_count = 0
            
            def _clean(val):
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return None
                res = str(val).strip()
                return res if res else None

            for match in proposed_matches:
                row = match['row']
                prop = match['prop']
                
                prev_erp = prop.unit_id_erp
                new_erp = _normalize_id(_clean(row.get('EnhetID')))
                
                # Apply updates
                if new_erp: prop.unit_id_erp = new_erp
                prop.lokalisering_id = _normalize_id(_clean(row.get('Lokasjonskode'))) or prop.lokalisering_id
                prop.name = _clean(row.get('Enhetsnavn')) or prop.name
                prop.affiliation = _clean(row.get('Tilhørighet'))
                
                def _safe_int(v):
                    cv = _clean(v)
                    if not cv: return None
                    try: return int(re.sub(r'[^\d]', '', str(cv)))
                    except: return None

                prop.budgeted_places = _safe_int(row.get('Antall budsjetterte plasser') or row.get('Antall_budsjetterte_plasser'))
                gk = _safe_int(row.get('Antall_GK_plasser'))
                if gk is not None:
                    prop.approved_places = gk
                prop.legal_basis = _clean(row.get('Hjemler'))
                prop.ownership_type = _clean(row.get('Eierskapenhet'))
                prop.region = _clean(row.get('Region')) or prop.region
                prop.municipality = _clean(row.get('Kommune')) or prop.municipality
                prop.postal_code = _clean(row.get('Postnummer')) or prop.postal_code
                prop.city = _clean(row.get('Poststed')) or prop.city
                prop.org_number = _clean(row.get('Orgnr')) or prop.org_number
                # Avdeling vs institusjon (jf. minnefil § 27–28)
                prop.unit_short_type = _clean(row.get('Enhetskorttype')) or prop.unit_short_type
                prop.unit_type_derived = _clean(row.get('Enhetstype (Utledet)')) or prop.unit_type_derived
                # Organisatorisk forelder: TilhørighetEnhetID = ERP-ID til overordnet institusjon
                parent_id = _normalize_id(_clean(row.get('TilhørighetEnhetID')))
                if parent_id:
                    prop.parent_unit_id_erp = parent_id
                
                # Atomic Audit Metadata + Birk-spesifikke felt
                if not prop.external_data: prop.external_data = {}
                ext = prop.external_data.copy()
                ext['last_match_method'] = match['method']
                ext['last_match_score'] = match['score']
                ext['edon2_import_date'] = datetime.utcnow().isoformat()
                tilhorighet2 = _clean(row.get('Tilhorighet2'))
                if tilhorighet2:
                    ext['birk_tilhorighet2'] = tilhorighet2
                prop.external_data = ext
                
                updated_count += 1
                
                audit_data.append({
                    'property_id': str(prop.property_id),
                    'eiendom_navn': prop.name,
                    'prev_unit_id_erp': prev_erp,
                    'proposed_unit_id_erp': new_erp,
                    'match_method': match['method'],
                    'score': match['score'],
                    'source_lokasjonskode': row.get('Lokasjonskode'),
                    'source_address': row.get('Adresse')
                })

            # Write Audit CSV
            audit_file = "match_audit_log.csv"
            with open(audit_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'property_id', 'eiendom_navn', 'prev_unit_id_erp', 
                    'proposed_unit_id_erp', 'match_method', 'score', 
                    'source_lokasjonskode', 'source_address'
                ], delimiter=';')
                writer.writeheader()
                writer.writerows(audit_data)

            await db.commit()
            return {
                "status": "success", 
                "updated": updated_count, 
                "audit_file": audit_file,
                "total_rows": len(df)
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"e-don2 import failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def import_text_csv(db: AsyncSession, file_content: bytes, category: str = "Imported") -> Dict[str, Any]:
        """
        Generic importer for text content from CSV.
        Expected columns: 'content', and optional 'metadata', 'source_file'.
        """
        try:
            content_sample = file_content[:1000].decode('utf-8', errors='ignore')
            delimiter = ';' if ';' in content_sample else ','
            
            df = pd.read_csv(io.BytesIO(file_content), sep=delimiter)
            
            imported_count = 0
            for _, row in df.iterrows():
                content = row.get('content') or row.get('Description') or row.get('Tekst')
                if not content or pd.isna(content):
                    continue
                
                text_obj = TextContent(
                    text_id=uuid.uuid4(),
                    content=str(content),
                    category=category,
                    source_type="csv_import",
                    additional_metadata={
                        "original_row": row.to_dict()
                    },
                    created_at=datetime.utcnow()
                )
                db.add(text_obj)
                imported_count += 1
            
            await db.commit()
            return {"status": "success", "imported": imported_count}
        except Exception as e:
            await db.rollback()
            logger.error(f"Text import failed: {str(e)}")
            return {"status": "error", "message": str(e)}
