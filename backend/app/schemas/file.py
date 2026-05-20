from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class FileBase(BaseModel):
    path: str
    file_type: Optional[str] = None
    content_type: Optional[str] = None

class File(FileBase):
    file_id: UUID
    contract_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
