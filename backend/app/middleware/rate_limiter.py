"""SpiderGPT In-Memory Rate Limiting Middleware."""
import time
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.core.config import settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.history: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Exclude health and docs from rate limiting
        path = request.url.path
        if path.startswith("/health") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization", "")
        client_key = f"{client_ip}:{auth_header[:25]}"

        now = time.time()
        minute_ago = now - 60.0

        # Purge old timestamps
        timestamps = self.history.get(client_key, [])
        valid_timestamps = [t for t in timestamps if t > minute_ago]

        if len(valid_timestamps) >= self.rpm:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                        "details": {"retry_after_seconds": int(60 - (now - valid_timestamps[0]))},
                    }
                },
            )

        valid_timestamps.append(now)
        self.history[client_key] = valid_timestamps

        response = await call_next(request)
        return response
