"""SpiderGPT User Profile Routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.user import UserProfileResponse, UserProfileUpdateRequest
from backend.app.services.user_service import UserService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_profile(
    current_user: User = Depends(get_current_user_from_token),
):
    return current_user


@router.put("/me", response_model=UserProfileResponse, summary="Update permitted profile fields")
async def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Updates display name, name, age, avatar, or default personality mode.

    Strictly forbids modifying subscription, usage counters, roles, or administrative privileges.
    """
    service = UserService(db)
    return await service.update_profile(current_user, payload)
