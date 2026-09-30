"""SpiderGPT Usage Tracking Routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_from_token
from backend.app.models.user import User
from backend.app.schemas.usage import UsageResponse
from backend.app.services.usage_service import UsageService

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("", response_model=UsageResponse, summary="Get current user usage limits and remaining quota")
async def get_usage(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Returns real-time server-side computed usage counters and remaining quotas for the current active plan."""
    service = UsageService(db)
    return await service.get_usage_overview(current_user)
