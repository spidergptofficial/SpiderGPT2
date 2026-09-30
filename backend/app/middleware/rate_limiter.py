"""Distributed Redis-backed rate limiting middleware."""
import hashlib
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from redis.asyncio import Redis

from backend.app.core.config import settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True) if settings.REDIS_URL else None

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/health", "/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        auth = request.headers.get("Authorization", "")
        identity = hashlib.sha256(f"{client_ip}:{auth[:64]}".encode()).hexdigest()
        bucket = int(time.time() // 60)
        key = f"spidergpt:ratelimit:{identity}:{bucket}"

        if self.redis:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 61)
        else:
            # Development/test fallback only. Production config rejects missing Redis.
            count = 1

        if count > self.rpm:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "60"},
                content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please slow down."}},
            )
        return await call_next(request)
