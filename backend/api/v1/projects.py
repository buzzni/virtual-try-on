from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from db.session import get_db
from models.project import Project
from models.user import User
from schemas.project import ProjectCreateRequest, ProjectResponse
from core.deps import get_current_user
from core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 중복 이름 체크 (같은 사용자 내에서)
    result = await db.execute(
        select(Project).where(
            Project.user_id == current_user.id,
            Project.name == request.name,
            Project.deleted_at.is_(None),
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise BadRequestException("Project with this name already exists")

    new_project = Project(
        collection_id=request.collection_id,
        user_id=current_user.id,
        name=request.name,
        shard_user_list=request.shard_user_list
    )
    
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    return new_project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundException("Project not found")
    
    return project


@router.get("", response_model=list[ProjectResponse])
async def get_projects(
    collection_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Project).where(
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    )
    
    if collection_id:
        query = query.where(Project.collection_id == collection_id)
    
    query = query.order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return projects
