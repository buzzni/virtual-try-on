from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from db.session import get_db
from models.subscription import Subscription, SubscriptionRecord
from models.user import User
from schemas.subscription import (
    SubscriptionCreateRequest,
    SubscriptionCancelRequest,
    SubscriptionPlanChangeRequest,
    SubscriptionResponse,
    SubscriptionRecordResponse
)
from core.deps import get_current_user
from core.exceptions import NotFoundException, BadRequestException
from datetime import datetime, timedelta

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise BadRequestException("Already have an active subscription")
    
    now = datetime.utcnow()
    new_subscription = Subscription(
        user_id=current_user.id,
        plan=request.plan,
        start_at=now,
        end_at=now + timedelta(days=30),
        next_billing_at=now + timedelta(days=30),
        payments=request.payments,
        status="active"
    )
    
    db.add(new_subscription)
    await db.flush()
    
    record = SubscriptionRecord(
        user_id=current_user.id,
        subscription_id=new_subscription.id,
        from_plan=None,
        to_plan=request.plan,
        payments=request.payments
    )
    db.add(record)
    
    await db.commit()
    await db.refresh(new_subscription)
    
    return new_subscription


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise NotFoundException("No active subscription found")
    
    old_plan = subscription.plan
    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    subscription.cancel_reason = request.cancel_reason
    subscription.updated_at = datetime.utcnow()
    
    record = SubscriptionRecord(
        user_id=current_user.id,
        subscription_id=subscription.id,
        from_plan=old_plan,
        to_plan=None,
        payments=subscription.payments
    )
    db.add(record)
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


@router.patch("/plan", response_model=SubscriptionResponse)
async def change_plan(
    request: SubscriptionPlanChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise NotFoundException("No active subscription found")
    
    old_plan = subscription.plan
    subscription.plan = request.new_plan
    subscription.payments = request.payments
    subscription.updated_at = datetime.utcnow()
    
    record = SubscriptionRecord(
        user_id=current_user.id,
        subscription_id=subscription.id,
        from_plan=old_plan,
        to_plan=request.new_plan,
        payments=request.payments
    )
    db.add(record)
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


@router.get("/history", response_model=List[SubscriptionRecordResponse])
async def get_subscription_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SubscriptionRecord)
        .where(SubscriptionRecord.user_id == current_user.id)
        .order_by(SubscriptionRecord.created_at.desc())
    )
    records = result.scalars().all()
    
    return records


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise NotFoundException("No active subscription found")
    
    return subscription
