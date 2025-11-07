"""Application-wide logging helpers built on structlog."""

from __future__ import annotations

from logging.config import dictConfig
from typing import TYPE_CHECKING, cast

import structlog
import structlog.types
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

from app.core.config import Settings, get_settings

if TYPE_CHECKING:
    from structlog.typing import FilteringBoundLogger


def setup_logging(settings: Settings | None = None, *, force: bool = False) -> None:
    """Configure structlog and stdlib logging."""

    settings = settings or get_settings()

    already_configured = structlog.is_configured()
    if already_configured and not force:
        return

    if already_configured and force:
        structlog.reset_defaults()

    log_level = settings.log_level

    timestamper = structlog.processors.TimeStamper(fmt="iso", key="timestamp")
    shared_processors: list[structlog.types.Processor] = [
        merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        timestamper,
    ]

    renderer: structlog.types.Processor
    if settings.log_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structlog": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        renderer,
                    ],
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "structlog",
                    "level": log_level,
                },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": log_level, "propagate": True},
                "uvicorn": {"handlers": ["default"], "level": log_level, "propagate": False},
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
            },
        }
    )

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    clear_contextvars()


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Return a structlog logger bound to the given name."""

    if not structlog.is_configured():
        setup_logging()

    if name is None:
        return cast("FilteringBoundLogger", structlog.get_logger())
    return cast("FilteringBoundLogger", structlog.get_logger(name))


__all__ = ["setup_logging", "get_logger", "bind_contextvars", "clear_contextvars"]
