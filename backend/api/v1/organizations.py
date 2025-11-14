from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from uuid import UUID
from db.session import get_db
from models.organization import Organization
from models.user import User
from schemas.organization import (
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationResponse,
)
from core.deps import get_current_user
from core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreateRequest,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 중복 이름 체크
    result = await db.execute(
        select(Organization).where(
            Organization.name == request.name,
            Organization.deleted_at.is_(None),
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise BadRequestException("Organization with this name already exists")

    organization = Organization(name=request.name)
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    return organization


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Organization)
        .where(Organization.deleted_at.is_(None))
        .order_by(Organization.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    organization = await _get_organization_or_404(db, organization_id)
    return organization


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    request: OrganizationUpdateRequest,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    organization = await _get_organization_or_404(db, organization_id)

    if request.name is not None:
        organization.name = request.name

    organization.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(organization)
    return organization


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    organization = await _get_organization_or_404(db, organization_id)
    organization.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Organization deleted"}


async def _get_organization_or_404(
    db: AsyncSession,
    organization_id: str,
) -> Organization:
    try:
        organization_uuid = UUID(str(organization_id))
    except ValueError:
        raise BadRequestException("Invalid organization id")

    result = await db.execute(
        select(Organization).where(
            Organization.id == organization_uuid,
            Organization.deleted_at.is_(None),
        )
    )
    organization = result.scalar_one_or_none()
    if not organization:
        raise NotFoundException("Organization not found")
    return organization
