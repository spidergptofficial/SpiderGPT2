"""SpiderGPT Configuration & Settings Management.

Loads configuration from environment variables with graceful defaults.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General Environment
    PROJECT_NAME: str = "SpiderGPT"
    PROJECT_TAGLINE: str = "Your AI Sidekick"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development, staging, or production")
    DEBUG: bool = Field(default=False)
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")

    APPLICATION_BASE_URL: str = Field(default="http://localhost:8000")
    FRONTEND_BASE_URL: str = Field(default="http://localhost:3000")
    ALLOWED_CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    )

    # Security & Tokens
    JWT_SECRET_KEY: str = Field(
        default="spidergpt-insecure-dev-secret-key-change-in-production-min32chars",
        description="HMAC secret for signing internal JWT session tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./spidergpt.db",
        description="Async connection string (e.g. postgresql+asyncpg://... or sqlite+aiosqlite:///...)",
    )
    DATABASE_ECHO: bool = Field(default=False)
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=5)

    # Supabase Integration (Optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Redis (Optional)
    REDIS_URL: Optional[str] = None

    # Storage (local / supabase / s3)
    STORAGE_PROVIDER: str = Field(default="local")
    STORAGE_BUCKET_NAME: str = Field(default="spidergpt-assets")
    STORAGE_LOCAL_DIR: str = Field(default="./uploads")

    # AI Providers Configuration
    AI_PROVIDER: str = Field(default="gemini", description="gemini, openai, openrouter, or deepseek")
    FALLBACK_AI_PROVIDER: Optional[str] = Field(default=None)

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = Field(default="gemini-3.8-flash")

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = Field(default="anthropic/claude-3.5-sonnet")

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat")

    # Image Provider
    IMAGE_PROVIDER: str = Field(default="openai", description="openai, gemini, or mock")
    IMAGE_MODEL: str = Field(default="dall-e-3")

    # Web Search Provider
    WEB_SEARCH_PROVIDER: str = Field(default="duckduckgo", description="tavily, serper, or duckduckgo")
    WEB_SEARCH_API_KEY: Optional[str] = None

    # Payments: Razorpay (India / INR)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    # Payments: Stripe (Global / USD / EUR)
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Regional Settings
    DEFAULT_CURRENCY: str = Field(default="INR")
    TIMEZONE: str = Field(default="UTC")

    # Admin Users (Comma-separated emails or list)
    ADMIN_EMAILS: List[str] = Field(default_factory=lambda: ["admin@spidergpt.com", "spidergptofficial@gmail.com"])

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=120)

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("ADMIN_EMAILS", mode="before")
    @classmethod
    def assemble_admin_emails(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
