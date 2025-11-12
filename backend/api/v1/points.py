from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from db.session import get_db
from models.point import Point, PointUsage
from models.project import Project
from models.user import User
from schemas.point import PointResponse, PointUpdateRequest, PointUsageResponse
from core.deps import get_current_user
from core.exceptions import BadRequestException, NotFoundException
from datetime import datetime

router = APIRouter(prefix="/points", tags=["points"])


@router.get("", response_model=PointResponse)
async def get_points(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Point).where(Point.user_id == current_user.id)
    )
    point = result.scalar_one_or_none()
    
    if not point:
        point = Point(
            user_id=current_user.id,
            credit=0,
            look_book_ticket=0,
            video_ticket=0
        )
        db.add(point)
        await db.commit()
        await db.refresh(point)
    
    return point


@router.post("/update", response_model=PointResponse)
async def update_points(
    request: PointUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if request.usage_method == "user_use" and not request.project_id:
        raise BadRequestException("project_id is required when usage_method is 'user_use'")
    
    if request.project_id:
        project_result = await db.execute(
            select(Project).where(
                Project.id == request.project_id,
                Project.user_id == current_user.id,
                Project.deleted_at.is_(None)
            )
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise NotFoundException("Project not found")
    
    result = await db.execute(
        select(Point).where(Point.user_id == current_user.id)
    )
    point = result.scalar_one_or_none()
    
    if not point:
        point = Point(
            user_id=current_user.id,
            credit=0,
            look_book_ticket=0,
            video_ticket=0
        )
        db.add(point)
        await db.flush()
    
    if request.credit is not None and request.credit != 0:
        new_credit = (point.credit or 0) + request.credit
        if new_credit < 0:
            raise BadRequestException("Insufficient credit balance")
        point.credit = new_credit
        usage = PointUsage(
            user_id=current_user.id,
            project_id=request.project_id,
            usage_type="credit",
            usage_method=request.usage_method,
            amount=request.credit,
            reason=request.reason
        )
        db.add(usage)
    
    if request.look_book_ticket is not None and request.look_book_ticket != 0:
        new_ticket = (point.look_book_ticket or 0) + request.look_book_ticket
        if new_ticket < 0:
            raise BadRequestException("Insufficient look_book_ticket balance")
        point.look_book_ticket = new_ticket
        usage = PointUsage(
            user_id=current_user.id,
            project_id=request.project_id,
            usage_type="look_book_ticket",
            usage_method=request.usage_method,
            amount=request.look_book_ticket,
            reason=request.reason
        )
        db.add(usage)
    
    if request.video_ticket is not None and request.video_ticket != 0:
        new_ticket = (point.video_ticket or 0) + request.video_ticket
        if new_ticket < 0:
            raise BadRequestException("Insufficient video_ticket balance")
        point.video_ticket = new_ticket
        usage = PointUsage(
            user_id=current_user.id,
            project_id=request.project_id,
            usage_type="video_ticket",
            usage_method=request.usage_method,
            amount=request.video_ticket,
            reason=request.reason
        )
        db.add(usage)
    
    point.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(point)
    
    return point


@router.get("/usage", response_model=List[PointUsageResponse])
async def get_point_usage(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PointUsage)
        .where(PointUsage.user_id == current_user.id)
        .order_by(PointUsage.created_at.desc())
        .limit(limit)
    )
    usages = result.scalars().all()
    
    return usages
