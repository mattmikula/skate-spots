"""Unit tests for the in-memory rate limiter."""

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.rate_limiter import RateLimitRule, RateLimiter, rate_limit_dependency, rate_limited


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter()
    rule = RateLimitRule(scope="test", limit=2, window_seconds=60)

    allowed, retry_after = limiter.check(
        identifier="client", scope=rule.scope, limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is True
    assert retry_after == 0

    allowed, retry_after = limiter.check(
        identifier="client", scope=rule.scope, limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is True
    assert retry_after == 0

    allowed, retry_after = limiter.check(
        identifier="client", scope=rule.scope, limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is False
    assert retry_after > 0

    limiter.reset()
    allowed, retry_after = limiter.check(
        identifier="client", scope=rule.scope, limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is True
    assert retry_after == 0


def test_rate_limiter_tracks_scopes_independently() -> None:
    limiter = RateLimiter()
    rule = RateLimitRule(scope="test", limit=1, window_seconds=60)

    allowed, _ = limiter.check(
        identifier="client", scope=rule.scope, limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is True

    allowed, retry_after = limiter.check(
        identifier="client", scope="other", limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is True
    assert retry_after == 0

    allowed, retry_after = limiter.check(
        identifier="client", scope=rule.scope, limit=rule.limit, window_seconds=rule.window_seconds
    )
    assert allowed is False
    assert retry_after > 0


@pytest.mark.asyncio
async def test_rate_limit_dependency_blocks_when_limit_exceeded() -> None:
    """The generated dependency should raise when the limit is exhausted."""

    rule = RateLimitRule(scope="dependency-test", limit=2, window_seconds=60)
    dependency = rate_limit_dependency(rule)
    request = Request({"type": "http", "client": ("203.0.113.1", 1234), "headers": []})

    await dependency(request)
    await dependency(request)

    with pytest.raises(HTTPException) as excinfo:
        await dependency(request)

    assert excinfo.value.status_code == 429
    assert "rate limit" in excinfo.value.detail.lower()
    assert "Retry-After" in excinfo.value.headers


def test_rate_limited_returns_depends_instance() -> None:
    """`rate_limited` should create a FastAPI dependency for a rule."""

    rule = RateLimitRule(scope="depends", limit=1, window_seconds=1)
    dependency = rate_limited(rule)

    assert dependency.dependency is not None
    assert callable(dependency.dependency)
