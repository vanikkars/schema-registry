"""Main FastAPI application for Schema Registry service."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api import router

app = FastAPI(
    title="Schema Registry Service",
    description="FastAPI service for managing data contracts in AWS Glue Schema Registry",
    version="1.0.0",
)

# Include routers
app.include_router(router)


@app.get("/", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Schema Registry Service",
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )