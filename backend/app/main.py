"""SpiderGPT - “Your AI Sidekick” Backend Application Entrypoint.

Production-grade FastAPI application with OpenAPI documentation,
multi-provider AI abstraction, server-side usage enforcement, and payment gateways.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.database import init_db, async_session_factory
from backend.app.core.exceptions import SpiderGPTException
from backend.app.core.logging import logger
from backend.app.middleware.error_handler import (
    spidergpt_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from backend.app.middleware.rate_limiter import RateLimiterMiddleware
from backend.app.middleware.request_logging import RequestLoggingMiddleware
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.routes import api_v1_router, system_router


TAGS_METADATA = [
    {"name": "Authentication", "description": "Google OAuth session verification, JWT tokens, and identity management."},
    {"name": "Profile", "description": "User profile viewing and safe parameter updates."},
    {"name": "Onboarding", "description": "Onboarding status verification and progression tracking."},
    {"name": "Spider", "description": "Personal AI companion management (Single-Spider enforcement, appearances, modes)."},
    {"name": "Chat", "description": "Real-time conversation interactions and SSE streaming with context memory."},
    {"name": "Conversations", "description": "Conversation lifecycle management and ownership checks."},
    {"name": "Saved", "description": "Saved message bookmarks and references."},
    {"name": "Images", "description": "AI image generation, asset metadata, and quota tracking."},
    {"name": "Search", "description": "Real-time web search integration."},
    {"name": "Research", "description": "Autonomous asynchronous Deep Research workflows."},
    {"name": "Usage", "description": "Server-side atomic quota verification and remaining balance reporting."},
    {"name": "Subscriptions", "description": "Tiered plans (FREE, PRO, PLUS) and active subscription management."},
    {"name": "Payments", "description": "Provider-independent checkout and payment verification (Razorpay & Stripe)."},
    {"name": "Webhooks", "description": "Cryptographically verified, idempotent webhook ingestion."},
    {"name": "Settings", "description": "System diagnostics, health checks, and administrator configuration."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing SpiderGPT Backend (%s environment)...", settings.ENVIRONMENT)
    try:
        await init_db()
        # Seed default subscription plans
        async with async_session_factory() as session:
            plan_repo = PlanRepository(session)
            await plan_repo.seed_plans_if_empty()
            await session.commit()
        logger.info("SpiderGPT database tables and plans ready.")
    except Exception as e:
        logger.error("Failed during database initialization: %s", str(e))
    yield
    logger.info("Shutting down SpiderGPT Backend.")


app = FastAPI(
    title="SpiderGPT API",
    description="Backend API for SpiderGPT - “Your AI Sidekick”. Production-ready backend supporting multi-provider AI, personal Spider customization, subscription limits, and deep research.",
    version=settings.VERSION,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 1. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Custom Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# 3. Exception Handlers
app.add_exception_handler(SpiderGPTException, spidergpt_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 4. Route Registration
app.include_router(system_router)
app.include_router(api_v1_router)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive OpenAPI documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
