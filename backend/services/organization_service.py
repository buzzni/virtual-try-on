from typing import Optional
from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.organization import Organization
from core.exceptions import NotFoundException


async def get_or_create_organization(
    db: AsyncSession,
    organization_name: Optional[str]
) -> Optional[Organization]:
    if organization_name is None:
        return None

    normalized = organization_name.strip()
    if not normalized:
        return None

    result = await db.execute(
        select(Organization).where(
            Organization.name == normalized,
            Organization.deleted_at.is_(None)
        )
    )
    organization = result.scalar_one_or_none()
    if organization:
        return organization

    organization = Organization(name=normalized)
    if getattr(organization, "id", None) is None:
        organization.id = uuid.uuid4()
    db.add(organization)
    await db.flush()

    return organization


async def get_organization_by_id(
    db: AsyncSession,
    organization_id: Optional[UUID]
) -> Optional[Organization]:
    if organization_id is None:
        return None

    result = await db.execute(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.deleted_at.is_(None)
        )
    )
    organization = result.scalar_one_or_none()
    if not organization:
        raise NotFoundException("Organization not found")
    return organization
