"""Main FastAPI application for Schema Registry service."""

import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from registry_api.app.api import router


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


app = FastAPI(
    title="Schema Registry Service",
    description="FastAPI service for managing data contracts in AWS Glue Schema Registry",
    version="1.0.0",
    default_response_class=PrettyJSONResponse,
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
    return PrettyJSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "registry_api.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )