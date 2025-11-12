from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class SubscriptionCreateRequest(BaseModel):
    plan: str
    payments: Optional[Dict[str, Any]] = None


class SubscriptionCancelRequest(BaseModel):
    cancel_reason: Optional[str] = None


class SubscriptionPlanChangeRequest(BaseModel):
    new_plan: str
    payments: Optional[Dict[str, Any]] = None


class SubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan: Optional[str]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    next_billing_at: Optional[datetime]
    payments: Optional[Dict]
    invoices: Optional[Dict]
    cancel_reason: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionRecordResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_id: Optional[UUID]
    from_plan: Optional[str]
    to_plan: Optional[str]
    payments: Optional[Dict]
    created_at: datetime
    
    class Config:
        from_attributes = True
