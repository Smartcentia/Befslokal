
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ConflictDetail(BaseModel):
    db: Any
    csv: Any

class ConflictRow(BaseModel):
    row_key: str
    diffs: Dict[str, ConflictDetail]
    row_data: Dict[str, Any]

class ImportAnalysisResponse(BaseModel):
    total_rows: int
    new_records: List[Dict[str, Any]]
    conflicts: List[ConflictRow]
    identical: int
    new_columns: List[str]

class ImportRequest(BaseModel):
    import_id: Optional[str] = None
    update_conflicts: bool = False
