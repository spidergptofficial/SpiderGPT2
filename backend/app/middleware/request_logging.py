"""SpiderGPT Structured Request Logging Middleware."""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend.app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:10]}")
        request.state.request_id = req_id

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Don't log spammy doc asset requests
        path = request.url.path
        if not (path.endswith(".png") or path.endswith(".ico") or path.endswith(".js") or path.endswith(".css")):
            logger.info(
                "[%s] %s %s -> %d (%.2fms)",
                req_id,
                request.method,
                path,
                response.status_code,
                duration_ms,
            )

        response.headers["X-Request-ID"] = req_id
        return response
