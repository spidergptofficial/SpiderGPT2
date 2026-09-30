"""SpiderGPT FastAPI application entrypoint."""
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
    spidergpt_exception_handler, validation_exception_handler,
    http_exception_handler, generic_exception_handler,
)
from backend.app.middleware.rate_limiter import RateLimiterMiddleware
from backend.app.middleware.request_logging import RequestLoggingMiddleware
from backend.app.repositories.plan_repo import PlanRepository
from backend.app.routes import api_v1_router, system_router

TAGS_METADATA = [
    {"name": "Authentication", "description": "Authentication and identity management."},
    {"name": "Profile", "description": "User profile management."},
    {"name": "Onboarding", "description": "Onboarding lifecycle."},
    {"name": "Spider", "description": "Personal Spider management."},
    {"name": "Chat", "description": "Conversation interactions and streaming."},
    {"name": "Conversations", "description": "Conversation lifecycle."},
    {"name": "Saved", "description": "Saved messages."},
    {"name": "Images", "description": "AI image generation."},
    {"name": "Search", "description": "Web search."},
    {"name": "Research", "description": "Durable Deep Research jobs."},
    {"name": "Usage", "description": "Server-side usage enforcement."},
    {"name": "Subscriptions", "description": "Subscription management."},
    {"name": "Payments", "description": "Checkout and payment verification."},
    {"name": "Webhooks", "description": "Verified webhook ingestion."},
    {"name": "Settings", "description": "Health and administrator diagnostics."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SpiderGPT Backend (%s)", settings.ENVIRONMENT)
    try:
        if settings.ENVIRONMENT in {"development", "test"}:
            await init_db()
            async with async_session_factory() as session:
                plan_repo = PlanRepository(session)
                await plan_repo.seed_plans_if_empty()
                await session.commit()
            logger.info("Development database schema/plans initialized.")
        else:
            logger.info("Production/staging startup: migrations must be applied separately; no create_all/auto-seeding.")
    except Exception:
        logger.exception("Database startup validation failed.")
        raise
    yield
    logger.info("Shutting down SpiderGPT Backend.")


app = FastAPI(
    title="SpiderGPT API",
    description="Backend API for SpiderGPT - Your AI Sidekick.",
    version=settings.VERSION,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

app.add_exception_handler(SpiderGPTException, spidergpt_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(system_router)
app.include_router(api_v1_router)


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
