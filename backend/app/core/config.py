"""SpiderGPT configuration and production safety checks."""
from pathlib import Path
from typing import Annotated, List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "SpiderGPT"
    PROJECT_TAGLINE: str = "Your AI Sidekick"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    APPLICATION_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    ALLOWED_CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    JWT_SECRET_KEY: str = Field(
        default="spidergpt-insecure-dev-secret-key-change-in-production-min32chars"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = "sqlite+aiosqlite:///./spidergpt.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    REDIS_URL: Optional[str] = None

    STORAGE_PROVIDER: str = "local"
    STORAGE_BUCKET_NAME: str = "spidergpt-assets"
    STORAGE_LOCAL_DIR: str = "./uploads"

    AI_PROVIDER: str = "gemini"
    FALLBACK_AI_PROVIDER: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"

    IMAGE_PROVIDER: str = "openai"
    IMAGE_MODEL: str = "dall-e-3"
    WEB_SEARCH_PROVIDER: str = "duckduckgo"
    WEB_SEARCH_API_KEY: Optional[str] = None

    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    RAZORPAY_PLAN_PRO_MONTHLY: Optional[str] = None
    RAZORPAY_PLAN_PRO_YEARLY: Optional[str] = None
    RAZORPAY_PLAN_PLUS_MONTHLY: Optional[str] = None
    RAZORPAY_PLAN_PLUS_YEARLY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    DEFAULT_CURRENCY: str = "INR"
    TIMEZONE: str = "UTC"
    ADMIN_EMAILS: Annotated[List[str], NoDecode] = Field(default_factory=list)
    RATE_LIMIT_PER_MINUTE: int = 120

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

    @model_validator(mode="after")
    def validate_environment(self):
        env = self.ENVIRONMENT.lower().strip()
        if env not in {"development", "staging", "production", "test"}:
            raise ValueError("ENVIRONMENT must be development, staging, production, or test")

        if env == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if "*" in self.ALLOWED_CORS_ORIGINS:
                raise ValueError("Wildcard CORS is forbidden in production")
            if not self.ALLOWED_CORS_ORIGINS:
                raise ValueError("At least one explicit CORS origin is required in production")
            if self.JWT_SECRET_KEY.startswith("spidergpt-insecure-") or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("A strong JWT_SECRET_KEY is required in production")
            if not self.DATABASE_URL.startswith(("postgresql+asyncpg://", "postgresql://")):
                raise ValueError("Production requires PostgreSQL via asyncpg")
            if self.STORAGE_PROVIDER.lower() != "supabase":
                raise ValueError("Production currently requires STORAGE_PROVIDER=supabase")
            if not self.SUPABASE_SERVICE_ROLE_KEY or not self.STORAGE_BUCKET_NAME:
                raise ValueError("Supabase service-role storage credentials are required in production")
            if self.AI_PROVIDER.lower() == "gemini" and not self.GEMINI_API_KEY:
                raise ValueError("Configured production AI provider is missing its API key")
            if self.AI_PROVIDER.lower() == "openai" and not self.OPENAI_API_KEY:
                raise ValueError("Configured production AI provider is missing its API key")
            if self.AI_PROVIDER.lower() == "openrouter" and not self.OPENROUTER_API_KEY:
                raise ValueError("Configured production AI provider is missing its API key")
            if self.AI_PROVIDER.lower() == "deepseek" and not self.DEEPSEEK_API_KEY:
                raise ValueError("Configured production AI provider is missing its API key")
            if self.IMAGE_PROVIDER.lower() == "mock":
                raise ValueError("Mock image provider is forbidden in production")
            if self.IMAGE_PROVIDER.lower() == "openai" and not self.OPENAI_API_KEY:
                raise ValueError("Configured production image provider is missing OPENAI_API_KEY")
            if self.IMAGE_PROVIDER.lower() == "gemini" and not self.GEMINI_API_KEY:
                raise ValueError("Configured production image provider is missing GEMINI_API_KEY")
            if self.WEB_SEARCH_PROVIDER.lower() in {"tavily", "serper"} and not self.WEB_SEARCH_API_KEY:
                raise ValueError("Configured production search provider is missing WEB_SEARCH_API_KEY")
            if not self.SUPABASE_URL or not self.SUPABASE_ANON_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY are required in production")
            if not self.ADMIN_EMAILS:
                raise ValueError("ADMIN_EMAILS must be explicitly configured in production")
            if not self.REDIS_URL:
                raise ValueError("REDIS_URL is required in production for distributed rate limiting")
            if self.RAZORPAY_KEY_ID or self.RAZORPAY_KEY_SECRET:
                if not (self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET and self.RAZORPAY_WEBHOOK_SECRET):
                    raise ValueError("Configured Razorpay requires key ID, key secret, and webhook secret")
                if not all((self.RAZORPAY_PLAN_PRO_MONTHLY, self.RAZORPAY_PLAN_PRO_YEARLY, self.RAZORPAY_PLAN_PLUS_MONTHLY, self.RAZORPAY_PLAN_PLUS_YEARLY)):
                    raise ValueError("Configured Razorpay requires recurring plan IDs for Pro/Plus monthly/yearly")
            if not ((self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET) or (self.STRIPE_SECRET_KEY and self.STRIPE_PUBLISHABLE_KEY)):
                raise ValueError("At least one production payment provider must be fully configured")
            if self.STRIPE_SECRET_KEY or self.STRIPE_PUBLISHABLE_KEY:
                if not (self.STRIPE_SECRET_KEY and self.STRIPE_PUBLISHABLE_KEY and self.STRIPE_WEBHOOK_SECRET):
                    raise ValueError("Configured Stripe requires secret key, publishable key, and webhook secret")
        return self


settings = Settings()
