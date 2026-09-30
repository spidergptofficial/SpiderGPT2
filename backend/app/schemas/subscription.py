"""SpiderGPT Subscription Response and Request Schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    plan_code: str
    plan_name: str
    provider: str
    provider_customer_id: Optional[str] = None
    provider_subscription_id: Optional[str] = None
    billing_period: str
    currency: str
    amount: int
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CancelSubscriptionRequest(BaseModel):
    reason: Optional[str] = None
    cancel_immediately: bool = False
