from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from models.user import User
from core.security import verify_token
from core.exceptions import UnauthorizedException
from uuid import UUID

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise UnauthorizedException()
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException()
    
    result = await db.execute(select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise UnauthorizedException()
    
    return user
