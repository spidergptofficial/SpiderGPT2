"""SpiderGPT User & Profile Schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    auth_provider_id: str
    email: EmailStr
    display_name: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    onboarding_completed: bool
    personality_mode: str
    default_mode: str
    role: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UserProfileUpdateRequest(BaseModel):
    """Allowed user profile fields. Strictly prevents modifying subscription, roles, usage, etc."""
    display_name: Optional[str] = Field(None, max_length=128)
    name: Optional[str] = Field(None, max_length=128)
    age: Optional[int] = Field(None, ge=1, le=150)
    avatar_url: Optional[str] = Field(None, max_length=512)
    personality_mode: Optional[str] = Field(None, max_length=32)
    default_mode: Optional[str] = Field(None, max_length=32)


class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    profile_completed: bool
    spider_created: bool
    has_active_subscription: bool
    current_plan: str
    personality_mode: str
