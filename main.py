"""Main FastAPI application entry point."""

from fastapi import FastAPI

from app.routers import skate_spots

app = FastAPI(
    title="Skate Spots API",
    description="An API for sharing and discovering skateboarding spots",
    version="0.1.0",
)

app.include_router(skate_spots.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API status."""
    return {"message": "Welcome to the Skate Spots API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
