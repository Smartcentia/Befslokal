from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class UserMinimal(BaseModel):
    user_id: UUID
    name: Optional[str] = None
    email: str
    role: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserRead(UserMinimal):
    region: Optional[str] = None
    is_active: bool = True
