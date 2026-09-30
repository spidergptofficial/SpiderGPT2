"""SpiderGPT Administrator Configuration Routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import require_admin_user
from backend.app.models.user import User
from backend.app.schemas.system import AdminConfigUpdateRequest

router = APIRouter(prefix="/admin", tags=["Settings"])


@router.get("/config", summary="Retrieve active runtime provider and model configuration")
async def get_admin_config(
    admin_user: User = Depends(require_admin_user),
):
    return {
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": getattr(settings, f"{settings.AI_PROVIDER.upper()}_MODEL", None),
        "fallback_ai_provider": settings.FALLBACK_AI_PROVIDER,
        "image_provider": settings.IMAGE_PROVIDER,
        "image_model": settings.IMAGE_MODEL,
        "search_provider": settings.WEB_SEARCH_PROVIDER,
        "default_currency": settings.DEFAULT_CURRENCY,
        "timezone": settings.TIMEZONE,
    }


@router.patch("/config", summary="Dynamically update runtime configuration without restarting server")
async def update_admin_config(
    payload: AdminConfigUpdateRequest,
    admin_user: User = Depends(require_admin_user),
):
    if payload.ai_provider:
        settings.AI_PROVIDER = payload.ai_provider.lower().strip()
    if payload.fallback_ai_provider:
        settings.FALLBACK_AI_PROVIDER = payload.fallback_ai_provider.lower().strip()
    if payload.image_provider:
        settings.IMAGE_PROVIDER = payload.image_provider.lower().strip()
    if payload.search_provider:
        settings.WEB_SEARCH_PROVIDER = payload.search_provider.lower().strip()
    if payload.timezone:
        settings.TIMEZONE = payload.timezone.strip()

    return {
        "message": "Configuration updated successfully.",
        "active_ai_provider": settings.AI_PROVIDER,
        "fallback_ai_provider": settings.FALLBACK_AI_PROVIDER,
        "active_image_provider": settings.IMAGE_PROVIDER,
        "active_search_provider": settings.WEB_SEARCH_PROVIDER,
    }


@router.get("/users", summary="Admin: List registered users")
async def list_users(
    limit: int = 50,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "onboarding_completed": u.onboarding_completed,
            "created_at": u.created_at,
        }
        for u in users
    ]
