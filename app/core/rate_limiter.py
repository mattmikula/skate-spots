"""Simple in-memory rate limiting utilities."""

from __future__ import annotations

import math
import time
from collections import abc, defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Depends, HTTPException, Request, status


@dataclass(frozen=True)
class RateLimitRule:
    """Configuration for a rate limit rule."""

    scope: str
    limit: int
    window_seconds: int


class RateLimiter:
    """Track request counts for rate-limited operations."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._events: defaultdict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check(
        self,
        *,
        identifier: str,
        scope: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, float]:
        """Return whether the request is allowed and retry delay if blocked."""

        now = time.monotonic()
        key = (identifier, scope)

        with self._lock:
            timestamps = self._events[key]

            while timestamps and now - timestamps[0] >= window_seconds:
                timestamps.popleft()

            if len(timestamps) >= limit:
                retry_after = window_seconds - (now - timestamps[0])
                return False, max(0.0, retry_after)

            timestamps.append(now)
            return True, 0.0

    def reset(self) -> None:
        """Clear all tracked requests."""

        with self._lock:
            self._events.clear()


rate_limiter = RateLimiter()

AUTH_LOGIN_LIMIT = RateLimitRule(scope="auth:login", limit=5, window_seconds=60)
AUTH_REGISTER_LIMIT = RateLimitRule(scope="auth:register", limit=5, window_seconds=60)
SKATE_SPOT_WRITE_LIMIT = RateLimitRule(scope="skate-spots:write", limit=50, window_seconds=60)


def rate_limit_dependency(rule: RateLimitRule) -> abc.Callable[[Request], None]:
    """Create a FastAPI dependency that enforces a rate limit rule."""

    async def _dependency(request: Request) -> None:
        identifier = request.client.host if request.client else "anonymous"
        allowed, retry_after = rate_limiter.check(
            identifier=identifier,
            scope=rule.scope,
            limit=rule.limit,
            window_seconds=rule.window_seconds,
        )

        if not allowed:
            retry_after_header = str(max(1, math.ceil(retry_after)))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": retry_after_header},
            )

    return _dependency


def rate_limited(rule: RateLimitRule) -> Depends:
    """Return a dependency that enforces the provided rate limit rule."""

    return Depends(rate_limit_dependency(rule))


__all__ = [
    "AUTH_LOGIN_LIMIT",
    "AUTH_REGISTER_LIMIT",
    "RateLimitRule",
    "SKATE_SPOT_WRITE_LIMIT",
    "rate_limit_dependency",
    "rate_limited",
    "rate_limiter",
]
