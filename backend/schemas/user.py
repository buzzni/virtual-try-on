from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

UserTypeLiteral = Literal["user", "manager", "admin"]


class UserResponse(BaseModel):
    id: UUID
    email: Optional[str]
    name: Optional[str]
    last_name: Optional[str]
    profile_picture: Optional[str]
    phone_number: Optional[str]
    organization_name: Optional[str]
    terms_agreed: bool
    privacy_agreed: bool
    marketing_agreed: bool
    user_type: UserTypeLiteral
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
    phone_number: Optional[str] = None
    organization_name: Optional[str] = None
    terms_agreed: Optional[bool] = None
    privacy_agreed: Optional[bool] = None
    marketing_agreed: Optional[bool] = None
