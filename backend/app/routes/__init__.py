"""SpiderGPT API Routes Module Export."""
from fastapi import APIRouter

from backend.app.routes.auth import router as auth_router
from backend.app.routes.profile import router as profile_router
from backend.app.routes.onboarding import router as onboarding_router
from backend.app.routes.spider import router as spider_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.conversations import router as conversations_router
from backend.app.routes.saved import router as saved_router
from backend.app.routes.images import router as images_router
from backend.app.routes.search import router as search_router
from backend.app.routes.research import router as research_router
from backend.app.routes.usage import router as usage_router
from backend.app.routes.subscriptions import router as subscriptions_router
from backend.app.routes.payments import router as payments_router
from backend.app.routes.webhooks import router as webhooks_router
from backend.app.routes.admin import router as admin_router
from backend.app.routes.system import router as system_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(profile_router)
api_v1_router.include_router(onboarding_router)
api_v1_router.include_router(spider_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(saved_router)
api_v1_router.include_router(images_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(usage_router)
api_v1_router.include_router(subscriptions_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(admin_router)

__all__ = ["api_v1_router", "system_router"]
