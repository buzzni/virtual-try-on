from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserResponse(BaseModel):
    id: UUID
    email: Optional[str]
    name: Optional[str]
    last_name: Optional[str]
    profile_picture: Optional[str]
    language: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None
    language: Optional[str] = None
