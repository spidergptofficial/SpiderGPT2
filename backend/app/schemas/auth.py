"""SpiderGPT Auth Schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = Field(None, description="Google OAuth ID Token from Google Sign-In SDK")
    access_token: Optional[str] = Field(None, description="OAuth Access Token if using Supabase Auth or direct flow")
    email: Optional[EmailStr] = Field(None, description="Optional override in dev/test mode")
    name: Optional[str] = Field(None, description="User full name")
    picture: Optional[str] = Field(None, description="Avatar image URL")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    onboarding_completed: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str
