"""SpiderGPT Usage Schemas."""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class CustomizationLimitsSchema(BaseModel):
    name_change_limit: int  # -1 represents unlimited
    name_changes_used: int
    name_changes_remaining: int
    appearance_change_limit: int  # -1 represents unlimited
    appearance_changes_used: int
    appearance_changes_remaining: int
    custom_appearance_allowed: bool
    custom_appearances_created: int


class UsageResponse(BaseModel):
    plan: str
    plan_name: str
    date: str
    month: str

    daily_response_limit: int
    responses_used: int
    responses_remaining: int

    daily_image_limit: int
    images_used: int
    images_remaining: int

    monthly_customization_limits: CustomizationLimitsSchema
    customization_usage: Dict[str, int]

    features: Dict[str, Any]
