from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from models.user import User
from models.collection import Collection
from schemas.auth import SignupRequest, LoginRequest, OAuthRequest, TokenResponse, UserResponse
from core.security import create_access_token, get_password_hash, verify_password
from core.exceptions import UnauthorizedException, BadRequestException
import httpx
from configs import settings
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise BadRequestException("Email already registered")
    
    new_user = User(
        email=request.email,
        name=request.name,
        last_name=request.last_name,
        language=request.language,
        phone_number=request.phone_number,
        organization_name=request.organization_name,
        terms_agreed=request.terms_agreed,
        privacy_agreed=request.privacy_agreed,
        marketing_agreed=request.marketing_agreed,
    )
    
    db.add(new_user)
    await db.flush()
    
    # 기본 Collection 자동 생성
    default_collection = Collection(
        user_id=new_user.id,
        name="My First Collection"
    )
    db.add(default_collection)
    
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException("Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id
    )


@router.post("/oauth/{provider}", response_model=TokenResponse)
async def oauth_login(
    provider: str,
    request: OAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    if provider not in ["google", "kakao"]:
        raise BadRequestException(f"Unsupported provider: {provider}")
    
    if provider == "google":
        user_info = await verify_google_token(request.access_token)
    elif provider == "kakao":
        user_info = await verify_kakao_token(request.access_token)
    else:
        raise BadRequestException("Unsupported provider")
    
    result = await db.execute(
        select(User).where(User.email == user_info["email"], User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=user_info["email"],
            name=user_info.get("name"),
            profile_picture=user_info.get("picture"),
            google_social=user_info if provider == "google" else None,
            kakao_social=user_info if provider == "kakao" else None,
        )
        db.add(user)
        await db.flush()
        
        # 기본 Collection 자동 생성
        default_collection = Collection(
            user_id=user.id,
            name="My First Collection"
        )
        db.add(default_collection)
        
        await db.commit()
        await db.refresh(user)
    else:
        if provider == "google":
            user.google_social = user_info
        elif provider == "kakao":
            user.kakao_social = user_info
        user.updated_at = datetime.utcnow()
        await db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id
    )


async def verify_google_token(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            raise UnauthorizedException("Invalid Google token")


async def verify_kakao_token(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            kakao_account = response.json().get("kakao_account", {})
            return {
                "email": kakao_account.get("email"),
                "name": kakao_account.get("profile", {}).get("nickname"),
                "picture": kakao_account.get("profile", {}).get("profile_image_url"),
            }
        except httpx.HTTPError:
            raise UnauthorizedException("Invalid Kakao token")
