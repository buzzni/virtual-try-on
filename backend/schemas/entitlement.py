from pydantic import BaseModel
from uuid import UUID


class EntitlementResponse(BaseModel):
    """
    Point와 Subscription을 조합하여 동적으로 생성되는 응답
    """
    user_id: UUID
    subscription_active: bool
    look_book_remaining: int
    video_remaining: int
    credit_cached: int
