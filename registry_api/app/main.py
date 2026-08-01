"""Main FastAPI application composition root.

Sets up the FastAPI app, wires dependencies (adapters/use cases),
and mounts routers. This is the entry point (registry_api.app.main:app).
"""

import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from registry_api.adapters.inbound.http.router import create_router
from registry_api.adapters.outbound.aws_glue.schema_registry_adapter import (
    GlueSchemaRegistryAdapter,
)
from registry_api.application.use_cases import (
    RegisterSchemaUseCase,
    ListSchemasUseCase,
    GetSchemaUseCase,
    GetSchemaVersionsUseCase,
    GetSchemaVersionUseCase,
    DeleteSchemaUseCase,
)


class PrettyJSONResponse(JSONResponse):
    """Custom JSONResponse with pretty-printing (indentation and sorted keys)."""

    def render(self, content):
        """Render response with indentation for readability."""
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=False,
        ).encode("utf-8")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Wires up all adapters and use cases, mounts routers.

    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app
    app = FastAPI(
        title="Schema Registry Service",
        description="FastAPI service for managing data contracts in AWS Glue Schema Registry",
        version="1.0.0",
        default_response_class=PrettyJSONResponse,
    )

    # Instantiate outbound adapters (AWS Glue)
    schema_registry_adapter = GlueSchemaRegistryAdapter()

    # Instantiate use cases, injecting adapters (ports)
    register_schema_use_case = RegisterSchemaUseCase(
        schema_registry=schema_registry_adapter,
    )
    list_schemas_use_case = ListSchemasUseCase(
        schema_registry=schema_registry_adapter
    )
    get_schema_use_case = GetSchemaUseCase(
        schema_registry=schema_registry_adapter
    )
    get_schema_versions_use_case = GetSchemaVersionsUseCase(
        schema_registry=schema_registry_adapter
    )
    get_schema_version_use_case = GetSchemaVersionUseCase(
        schema_registry=schema_registry_adapter
    )
    delete_schema_use_case = DeleteSchemaUseCase(
        schema_registry=schema_registry_adapter
    )

    # Create and mount router with injected use cases
    router = create_router(
        register_schema_use_case=register_schema_use_case,
        list_schemas_use_case=list_schemas_use_case,
        get_schema_use_case=get_schema_use_case,
        get_schema_versions_use_case=get_schema_versions_use_case,
        get_schema_version_use_case=get_schema_version_use_case,
        delete_schema_use_case=delete_schema_use_case,
    )
    app.include_router(router)

    # Health check endpoints
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
        return {"status": "ok", "version": "2.0"}

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        return PrettyJSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(exc)},
        )

    return app


# Create the app instance (used by Dockerfile CMD and uvicorn)
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "registry_api.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )