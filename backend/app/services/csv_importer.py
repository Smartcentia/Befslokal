
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Dict, Any, Tuple, Optional
import io
import json
from uuid import UUID

from app.domains.core.models.party import Party
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract

class ImportAnalysis:
    def __init__(self):
        self.total_rows = 0
        self.new_records: List[Dict] = []
        self.conflicts: List[Dict] = []
        self.identical = 0
        self.new_columns: List[str] = []

def parse_csv_file(file_content: bytes, delimiter: str = None) -> List[Dict[str, Any]]:
    """
    Parse CSV file content into a list of dictionaries.
    Async-safe (CPU bound, but fast enough for small files).
    """
    try:
        content_str = file_content.decode('utf-8')
    except UnicodeDecodeError:
        content_str = file_content.decode('latin-1')

    if not delimiter:
        if ';' in content_str and content_str.count(';') > content_str.count(','):
            delimiter = ';'
        else:
            delimiter = ','

    df = pd.read_csv(io.StringIO(content_str), sep=delimiter)
    df = df.where(pd.notnull(df), None)
    
    return df.to_dict(orient='records')

def _get_model_fields(model_class) -> List[str]:
    return [c.name for c in model_class.__table__.columns]

def _compare_values(db_val: Any, csv_val: Any) -> bool:
    if db_val is None and csv_val is None:
        return True
    if db_val is None or csv_val is None:
        return False
    return str(db_val).strip() == str(csv_val).strip()

async def analyze_import(
    file_content: bytes, 
    entity_type: str, 
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Analyze CSV content against existing database records (Async).
    """
    rows = parse_csv_file(file_content)
    analysis = ImportAnalysis()
    analysis.total_rows = len(rows)
    
    if not rows:
        return analysis.__dict__

    # Determine Model and Keys
    if entity_type.lower() == 'party':
        Model = Party
        pk_field = 'orgnr'
        model_fields = _get_model_fields(Party)
    elif entity_type.lower() == 'property':
        Model = Property
        pk_field = 'name' 
        model_fields = _get_model_fields(Property)
    elif entity_type.lower() == 'contract':
        Model = Contract
        pk_field = 'contract_id'
        model_fields = _get_model_fields(Contract)
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")

    csv_columns = list(rows[0].keys())
    analysis.new_columns = [col for col in csv_columns if col not in model_fields]

    for row in rows:
        # Find match (Async)
        match = None
        stmt = None
        
        if entity_type.lower() == 'party' and row.get('orgnr'):
            stmt = select(Model).filter(Model.orgnr == str(row['orgnr']))
        elif entity_type.lower() == 'property':
            if all(k in row for k in ['gnr', 'bnr', 'municipality_code']):
                stmt = select(Model).filter(
                    Model.gnr == str(row['gnr']),
                    Model.bnr == str(row['bnr']),
                    Model.municipality_code == str(row['municipality_code'])
                )
            
            # Fallback: Address matching from Dim 2(T)
            if stmt is None and row.get('Dim 2(T)'):
                 addr_raw = row['Dim 2(T)']
                 if addr_raw:
                     # Simple split by comma, ignoring zip/city part
                     clean_addr = addr_raw.split(',')[0].strip()
                     stmt = select(Model).filter(func.lower(Model.address) == clean_addr.lower())
        
        if stmt is not None:
            result = await db.execute(stmt)
            match = result.scalar_one_or_none()
        
        if match:
            conflicts = {}
            has_diff = False
            
            for col in csv_columns:
                if col in model_fields:
                    db_val = getattr(match, col)
                    csv_val = row[col]
                    if not _compare_values(db_val, csv_val):
                        conflicts[col] = {"db": db_val, "csv": csv_val}
                        has_diff = True
            
            current_ext_data = match.external_data or {}
            for col in analysis.new_columns:
                db_val = current_ext_data.get(col)
                csv_val = row[col]
                if not _compare_values(db_val, csv_val):
                    conflicts[col] = {"db": db_val, "csv": csv_val}
                    has_diff = True

            if has_diff:
                analysis.conflicts.append({
                    "row_key": row.get(pk_field) or "N/A",
                    "diffs": conflicts,
                    "row_data": row
                })
            else:
                analysis.identical += 1
        else:
            analysis.new_records.append(row)

    return analysis.__dict__


async def import_csv_to_db(
    file_content: bytes,
    entity_type: str,
    db: AsyncSession,
    update_conflicts: bool = False
) -> Dict[str, Any]:
    """
    Execute the import (Async).
    """
    # Re-analyze to get categorized rows
    # In a real app we might pass the analysis result, but re-analyzing is safer for MVP stat correctness
    analysis_dict = await analyze_import(file_content, entity_type, db)
    
    imported_count = 0
    updated_count = 0
    
    Model = None
    if entity_type.lower() == 'party':
        Model = Party
    elif entity_type.lower() == 'property':
        Model = Property
    elif entity_type.lower() == 'contract':
        Model = Contract
    
    # Create New Records
    for row in analysis_dict['new_records']:
        model_fields = _get_model_fields(Model)
        data = {}
        ext_data = {}
        for k, v in row.items():
            if k in model_fields:
                data[k] = v
            else:
                ext_data[k] = v
        if ext_data:
            data['external_data'] = ext_data
            
        new_obj = Model(**data)
        db.add(new_obj)
        imported_count += 1
        
    # Update Conflicts
    if update_conflicts:
         for conflict in analysis_dict['conflicts']:
            row = conflict['row_data']
            stmt = None
            if entity_type.lower() == 'party':
                stmt = select(Model).filter(Model.orgnr == str(row['orgnr']))
            elif entity_type.lower() == 'property':
                 if all(k in row for k in ['gnr', 'bnr', 'municipality_code']):
                    stmt = select(Model).filter(
                        Model.gnr == str(row['gnr']),
                        Model.bnr == str(row['bnr']),
                        Model.municipality_code == str(row['municipality_code'])
                    )
            
            # Fallback: Address matching from Dim 2(T)
            if stmt is None and row.get('Dim 2(T)'):
                 addr_raw = row['Dim 2(T)']
                 if addr_raw:
                     # Simple split by comma
                     clean_addr = addr_raw.split(',')[0].strip()
                     stmt = select(Model).filter(func.lower(Model.address) == clean_addr.lower())
            
            if stmt is not None:
                result = await db.execute(stmt)
                match = result.scalar_one_or_none()
                
                if match:
                    current_ext = dict(match.external_data or {})
                    model_fields = _get_model_fields(Model)
                    for k, v in row.items():
                        if k in model_fields:
                            setattr(match, k, v)
                        else:
                            current_ext[k] = v
                    match.external_data = current_ext
                    updated_count += 1

    await db.commit()
    
    return {
        "status": "success",
        "imported": imported_count,
        "updated": updated_count,
        "ignored": len(analysis_dict['conflicts']) if not update_conflicts else 0
    }
