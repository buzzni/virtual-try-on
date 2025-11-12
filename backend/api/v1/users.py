from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from db.session import get_db
from models.user import User
from schemas.user import UserResponse, UserUpdateRequest
from core.deps import get_current_user
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if request.name is not None:
        current_user.name = request.name
    if request.last_name is not None:
        current_user.last_name = request.last_name
    if request.profile_picture is not None:
        current_user.profile_picture = request.profile_picture
    if request.language is not None:
        current_user.language = request.language
    
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.delete("/me")
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    현재 사용자 삭제 (Hard Delete)
    - FK CASCADE로 연관된 모든 데이터 자동 삭제:
      * entitlements
      * points, point_usage
      * collections, projects
      * subscriptions, subscription_record
    """
    await db.execute(
        delete(User).where(User.id == current_user.id)
    )
    await db.commit()
    
    return {"message": "User deleted successfully"}
