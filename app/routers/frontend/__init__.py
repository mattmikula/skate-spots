"""Frontend HTML routers."""

from fastapi import APIRouter

from . import (
    auth_pages,
    check_ins,
    comments,
    favorites,
    feed,
    home,
    notifications,
    profiles,
    ratings,
    sessions,
    spots,
)

# Create the aggregated router
router = APIRouter(tags=["frontend"])

# Include all sub-routers
router.include_router(home.router)
router.include_router(auth_pages.router)
router.include_router(profiles.router)
router.include_router(spots.router)
router.include_router(sessions.router)
router.include_router(check_ins.router)
router.include_router(ratings.router)
router.include_router(favorites.router)
router.include_router(comments.router)
router.include_router(notifications.router)
router.include_router(feed.router)

__all__ = ["router"]
