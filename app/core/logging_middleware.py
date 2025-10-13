"""Middleware that ensures each HTTP request is logged with context."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import bind_contextvars, clear_contextvars, get_logger

if TYPE_CHECKING:
    from fastapi import Request
    from starlette.types import ASGIApp


class RequestContextLogMiddleware(BaseHTTPMiddleware):
    """Attach request-scoped context and log the response outcome."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex
        clear_contextvars()
        client_ip = request.client.host if request.client else None
        bind_contextvars(
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
            client_ip=client_ip,
        )

        start = time.perf_counter()
        response = None

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            self._logger.exception(
                "request failed",
                duration_ms=round(duration_ms, 2),
                user_agent=request.headers.get("user-agent"),
            )
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000
            response.headers["X-Request-ID"] = request_id
            self._logger.info(
                "request completed",
                http_status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                user_agent=request.headers.get("user-agent"),
            )
            return response
        finally:
            clear_contextvars()
