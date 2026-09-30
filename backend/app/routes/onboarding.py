"""SpiderGPT Onboarding Status Routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.user import OnboardingStatusResponse
from backend.app.services.user_service import UserService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/status", response_model=OnboardingStatusResponse, summary="Get user onboarding completion status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_onboarding_status(current_user)
