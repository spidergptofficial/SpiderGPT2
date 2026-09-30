"""SpiderGPT System & Provider Diagnostics Routes."""
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.system import HealthResponse, ProvidersStatusResponse
from backend.app.providers.payments.factory import PaymentFactory
from backend.app.providers.ai.factory import AIFactory
from backend.app.services.mode_service import ModeService

router = APIRouter(tags=["Settings"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check():
    return {
        "status": "healthy",
        "app": "SpiderGPT Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/v1/system/providers", response_model=ProvidersStatusResponse, summary="Check configured provider capabilities without secrets")
async def get_providers_configuration():
    """Reports configuration presence for AI, payment, image, and search providers without leaking credentials."""
    ai_status = {
        "gemini": bool(settings.GEMINI_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY),
        "openrouter": bool(settings.OPENROUTER_API_KEY),
        "deepseek": bool(settings.DEEPSEEK_API_KEY),
    }

    payments_status = PaymentFactory.get_availability()

    search_status = {
        "tavily": bool(settings.WEB_SEARCH_API_KEY and settings.WEB_SEARCH_PROVIDER == "tavily"),
        "serper": bool(settings.WEB_SEARCH_API_KEY and settings.WEB_SEARCH_PROVIDER == "serper"),
        "duckduckgo": True,
        "configured": True,
    }

    image_status = {
        "openai": bool(settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }

    return {
        "ai": ai_status,
        "payments": payments_status,
        "search": search_status,
        "image": image_status,
        "active_ai_provider": AIFactory.resolve_active_provider_name(),
        "fallback_ai_provider": settings.FALLBACK_AI_PROVIDER,
        "active_search_provider": settings.WEB_SEARCH_PROVIDER,
        "active_image_provider": settings.IMAGE_PROVIDER,
    }


@router.get("/api/v1/system/modes", summary="List available Spider personality modes")
async def get_modes():
    return ModeService.get_all_modes()
