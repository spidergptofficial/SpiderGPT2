"""SpiderGPT Plan & Subscription Schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PlanFeatureSchema(BaseModel):
    feature_key: str
    feature_value: str
    description: str

    class Config:
        from_attributes = True


class PlanResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    monthly_price_inr: int
    yearly_price_inr: int
    monthly_price_usd: int
    yearly_price_usd: int
    regional_pricing: Dict[str, Any]
    daily_response_limit: int
    daily_image_limit: int
    monthly_name_change_limit: int
    monthly_appearance_change_limit: int
    custom_appearance_allowed: bool
    allowed_modes: List[str]
    deep_research_allowed: bool
    annual_monthly_equivalent_inr: int
    billing_notes: Dict[str, str]

    class Config:
        from_attributes = True


class PlanCreateUpdateRequest(BaseModel):
    code: str
    name: str
    description: str
    monthly_price_inr: int
    yearly_price_inr: int
    monthly_price_usd: int
    yearly_price_usd: int
    regional_pricing: Optional[Dict[str, Any]] = None
    daily_response_limit: int
    daily_image_limit: int
    monthly_name_change_limit: int
    monthly_appearance_change_limit: int
    custom_appearance_allowed: bool
    allowed_modes: List[str]
    deep_research_allowed: bool
    is_active: bool = True
