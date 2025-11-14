from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime
from schemas.user import UserTypeLiteral


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    last_name: Optional[str] = None
    language: str = "ko"
    phone_number: Optional[str] = None
    organization_name: Optional[str] = None
    terms_agreed: bool = False
    privacy_agreed: bool = False
    marketing_agreed: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OAuthRequest(BaseModel):
    provider: str
    access_token: str
    id_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID


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
    
    class Config:
        from_attributes = True
