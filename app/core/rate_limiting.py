import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import get_settings

settings = get_settings()

# Simple in-memory token bucket per IP+path
_buckets: Dict[Tuple[str, str], Tuple[int, float]] = {}

def rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    path = request.url.path
    key = (ip, path)
    capacity = settings.rate_limit_requests_per_minute
    now = time.time()
    tokens, last = _buckets.get(key, (capacity, now))
    # refill
    elapsed = now - last
    refill = int(elapsed * (capacity / 60.0))
    tokens = min(capacity, tokens + refill)
    if tokens <= 0:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    _buckets[key] = (tokens - 1, now)
