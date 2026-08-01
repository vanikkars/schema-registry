"""Dedicated Iceberg Table Creation HTTP Service.

This service is responsible for creating Iceberg tables in AWS Glue.
It's decoupled from the schema registry to allow independent deployment
and scaling.

Usage:
    uvicorn iceberg_creation_service.main:app --host 0.0.0.0 --port 8001
"""

import json
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from iceberg_creation_service.routers import tables
from iceberg_creation_service.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()


class PrettyJSONResponse(JSONResponse):
    """Custom JSON response with pretty formatting."""

    def render(self, content):
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=False,
        ).encode("utf-8")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Iceberg Table Creation Service",
        description="Service for creating and managing Iceberg tables in AWS Glue",
        version="1.0.0",
        default_response_class=PrettyJSONResponse,
    )

    @app.get("/", tags=["health"])
    async def health_check() -> dict:
        """Service health check."""
        return {
            "status": "healthy",
            "service": "Iceberg Table Creation Service",
            "version": "1.0.0",
        }

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "version": "1.0.0"}

    app.include_router(tables.router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {str(exc)}")
        return PrettyJSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "Internal server error",
                "error": str(exc),
            },
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "iceberg_creation_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )