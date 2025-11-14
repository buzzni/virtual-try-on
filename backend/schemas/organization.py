from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class OrganizationCreateRequest(BaseModel):
    name: str


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
