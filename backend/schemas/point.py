from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime


class PointResponse(BaseModel):
    user_id: UUID
    credit: int
    look_book_ticket: int
    video_ticket: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PointUpdateRequest(BaseModel):
    credit: Optional[int] = None
    look_book_ticket: Optional[int] = None
    video_ticket: Optional[int] = None
    usage_method: Literal["manual", "user_use", "purchase", "subscribe"]
    project_id: Optional[UUID] = None
    reason: Optional[str] = None


class PointUsageResponse(BaseModel):
    id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    job_id: Optional[UUID]
    usage_type: str
    usage_method: str
    amount: int
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
