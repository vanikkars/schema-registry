"""Dedicated Iceberg Table Creation HTTP Service (Domain-Driven Design).

This service is responsible for creating Iceberg tables in AWS Glue.
It's decoupled from the schema registry to allow independent deployment
and scaling.

Architecture: Domain-Driven Design
- Domain Layer: Core business logic, entities, value objects
- Application Layer: Use cases, orchestration, DTOs
- Infrastructure Layer: External dependencies (AWS Glue)
- Presentation Layer: HTTP API endpoints

Usage:
    uvicorn iceberg_creation_service.main:app --host 0.0.0.0 --port 8001
"""

import json
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from iceberg_creation_service.config import Settings
from iceberg_creation_service.infrastructure.repositories import AwsGlueIcebergTableRepository
from iceberg_creation_service.application.use_cases import (
    CreateTableUseCase,
    UpdateTableSchemaUseCase,
    GetTableInfoUseCase,
)
from iceberg_creation_service.presentation.routes import create_routes

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
    """Create and configure the FastAPI application with dependency injection."""
    app = FastAPI(
        title="Iceberg Table Creation Service",
        description="DDD-based service for creating and managing Iceberg tables in AWS Glue",
        version="2.0.0",
        default_response_class=PrettyJSONResponse,
    )

    # Initialize infrastructure layer
    repository = AwsGlueIcebergTableRepository(region=settings.aws_region)

    # Initialize application layer (use cases)
    create_table_use_case = CreateTableUseCase(repository)
    update_table_use_case = UpdateTableSchemaUseCase(repository)
    get_table_use_case = GetTableInfoUseCase(repository)

    # Initialize presentation layer
    table_routes = create_routes(
        create_table_use_case,
        update_table_use_case,
        get_table_use_case,
    )

    @app.get("/", tags=["health"])
    async def health_check() -> dict:
        """Service health check."""
        return {
            "status": "healthy",
            "service": "Iceberg Table Creation Service",
            "version": "2.0.0",
            "architecture": "Domain-Driven Design",
        }

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": "2.0.0",
        }

    # Include routes
    app.include_router(table_routes)

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return PrettyJSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "Internal server error",
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