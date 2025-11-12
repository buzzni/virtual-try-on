from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from models.point import Point
from models.subscription import Subscription
from models.user import User
from schemas.entitlement import EntitlementResponse
from core.deps import get_current_user

router = APIRouter(prefix="/entitlements", tags=["entitlements"])


@router.get("/me", response_model=EntitlementResponse)
async def get_my_entitlement(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Point와 Subscription 정보를 조합하여 Entitlement 응답 생성
    - subscription_active: 활성 구독 여부
    - look_book_remaining: point.look_book_ticket
    - video_remaining: point.video_ticket
    - credit_cached: point.credit
    """
    # Point 조회
    point_result = await db.execute(
        select(Point).where(Point.user_id == current_user.id)
    )
    point = point_result.scalar_one_or_none()
    
    # Subscription 조회
    subscription_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        )
    )
    subscription = subscription_result.scalar_one_or_none()
    
    # 응답 생성
    return EntitlementResponse(
        user_id=current_user.id,
        subscription_active=subscription is not None,
        look_book_remaining=point.look_book_ticket if point else 0,
        video_remaining=point.video_ticket if point else 0,
        credit_cached=point.credit if point else 0
    )
