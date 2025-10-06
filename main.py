"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import frontend, skate_spots

app = FastAPI(
    title="Skate Spots API",
    description="An API for sharing and discovering skateboarding spots",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(frontend.router)
app.include_router(skate_spots.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
