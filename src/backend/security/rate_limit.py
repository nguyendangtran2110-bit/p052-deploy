"""Small in-process sliding-window limiter for chatbot endpoints.

This is an immediate abuse/cost guard. Multi-replica deployments should back
the same interface with Redis or an API-gateway limiter for a global quota.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.backend.core.config import get_settings


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, *, limit: int, window_seconds: int, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - window_seconds
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= limit:
                return False
            timestamps.append(current)
            return True


chat_limiter = SlidingWindowLimiter()


def _is_chat_message_path(path: str) -> bool:
    if path.endswith("/chat") or path.endswith("/chat/messages"):
        return True
    return path.endswith("/messages") and (
        "/tickets/" in path or "/management/assistant/conversations/" in path
    )


def _client_key(request: Request) -> tuple[str, bool]:
    authorization = request.headers.get("authorization", "").strip()
    dev_identity = "|".join(
        filter(
            None,
            (
                request.headers.get("x-actor-role"),
                request.headers.get("x-actor-id"),
                request.headers.get("x-resident-id"),
            ),
        )
    )
    identity = authorization or dev_identity
    if identity:
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return f"authenticated:{digest}", True
    host = request.client.host if request.client else "unknown"
    return f"anonymous:{host}", False


class ChatRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if (
            not settings.chat_rate_limit_enabled
            or request.method != "POST"
            or not _is_chat_message_path(request.url.path)
        ):
            return await call_next(request)

        key, authenticated = _client_key(request)
        limit = (
            settings.chat_rate_limit_authenticated_requests
            if authenticated
            else settings.chat_rate_limit_anonymous_requests
        )
        if not chat_limiter.allow(
            key,
            limit=limit,
            window_seconds=settings.chat_rate_limit_window_seconds,
        ):
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited", "message": "Too many chatbot requests; please try again later."}},
                headers={"Retry-After": str(settings.chat_rate_limit_window_seconds)},
            )
        return await call_next(request)
