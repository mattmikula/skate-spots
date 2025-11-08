"""Main FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.logging_middleware import RequestContextLogMiddleware
from app.core.rate_limiter import rate_limiter
from app.routers import (
    activity,
    auth,
    check_ins,
    comments,
    favorites,
    follows,
    frontend,
    geocoding,
    notifications,
    ratings,
    sessions,
    skate_spots,
)

settings = get_settings()
setup_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    # Startup
    setup_logging(settings, force=True)
    logger.info("application startup complete", version=app.version)
    yield
    # Shutdown
    logger.info("application shutdown")


app = FastAPI(
    title="Skate Spots API",
    description="An API for sharing and discovering skateboarding spots",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextLogMiddleware)
app.state.rate_limiter = rate_limiter

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

media_directory = Path(settings.media_directory)
media_directory.mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url_path, StaticFiles(directory=media_directory), name="media")

# Include routers
app.include_router(frontend.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(activity.router)  # Has its own prefix: /api/v1/feed
app.include_router(favorites.router, prefix="/api/v1")
app.include_router(follows.router, prefix="/api/v1")
app.include_router(skate_spots.router, prefix="/api/v1")
app.include_router(ratings.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(geocoding.router, prefix="/api/v1")
app.include_router(check_ins.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
