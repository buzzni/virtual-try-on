from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CollectionCreateRequest(BaseModel):
    name: str


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = None


class CollectionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
