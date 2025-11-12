from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from db.session import get_db
from models.collection import Collection
from models.user import User
from schemas.collection import CollectionCreateRequest, CollectionUpdateRequest, CollectionResponse
from core.deps import get_current_user
from core.exceptions import NotFoundException
from datetime import datetime

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse)
async def create_collection(
    request: CollectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_collection = Collection(
        user_id=current_user.id,
        name=request.name
    )
    
    db.add(new_collection)
    await db.commit()
    await db.refresh(new_collection)
    
    return new_collection


@router.get("", response_model=List[CollectionResponse])
async def get_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Collection).where(
            Collection.user_id == current_user.id,
            Collection.deleted_at.is_(None)
        ).order_by(Collection.created_at.desc())
    )
    collections = result.scalars().all()
    
    return collections


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    request: CollectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == current_user.id,
            Collection.deleted_at.is_(None)
        )
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise NotFoundException("Collection not found")
    
    if request.name is not None:
        collection.name = request.name
    
    collection.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(collection)
    
    return collection
