import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int = 60) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self._window: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in ("/health", "/api/v1/health"):
            return await call_next(request)
        ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - 60.0
        self._window[ip] = [t for t in self._window[ip] if t > window_start]
        if len(self._window[ip]) >= self.per_minute:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Try again in a moment.",
                        "details": {"retry_after_seconds": 60},
                    },
                    "meta": {"request_id": request_id} if request_id else {},
                },
                headers={"Retry-After": "60"},
            )
        self._window[ip].append(now)
        return await call_next(request)
