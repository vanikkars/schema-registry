"""Iceberg Table Creation Service - FastAPI application."""

import json
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from iceberg_creation_service.adapters.aws_glue_adapter import AwsGlueIcebergAdapter
from iceberg_creation_service.application.use_cases import (
    CreateTableUseCase,
    UpdateTableSchemaUseCase,
    GetTableInfoUseCase,
)
from iceberg_creation_service.domain.exceptions import (
    InvalidTableError,
    TableNotFoundError,
    TableCreationError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        version="2.0.0",
        default_response_class=PrettyJSONResponse,
    )

    # Initialize adapters
    glue_adapter = AwsGlueIcebergAdapter()

    # Initialize use cases
    create_table_use_case = CreateTableUseCase(glue_adapter)
    update_table_use_case = UpdateTableSchemaUseCase(glue_adapter)
    get_table_use_case = GetTableInfoUseCase(glue_adapter)

    @app.get("/", tags=["health"])
    async def health_check() -> dict:
        """Service health check."""
        return {
            "status": "healthy",
            "service": "Iceberg Table Creation Service",
            "version": "2.0.0",
        }

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "version": "2.0.0"}

    @app.post("/api/v1/tables", status_code=status.HTTP_201_CREATED)
    async def create_table(contract: dict) -> dict:
        """Create an Iceberg table from a data contract."""
        try:
            logger.info(f"API: Creating table for {contract.get('name')}")
            result = await create_table_use_case.execute(contract)
            return {"data": result}
        except InvalidTableError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except TableCreationError as e:
            logger.error(f"Creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.post("/api/v1/tables/{table_name}/schema", status_code=status.HTTP_200_OK)
    async def update_table_schema(table_name: str, contract: dict) -> dict:
        """Update an existing table's schema."""
        try:
            logger.info(f"API: Updating table {table_name} with contract {contract.get('contract_id')}")
            result = await update_table_use_case.execute(table_name, contract)

            # Log detailed change information
            if result.get("status") == "updated":
                summary = result.get("change_summary", {})
                logger.info(f"Schema changes for {table_name}:")
                logger.info(f"  - Added columns: {summary.get('added', 0)}")
                logger.info(f"  - Removed columns: {summary.get('removed', 0)}")
                logger.info(f"  - Modified columns: {summary.get('modified', 0)}")
                logger.info(f"  - Version: {result.get('old_version')} → {result.get('new_version')}")

                # Log detailed changes
                changes = result.get("change_details", {})
                for col in changes.get("added_columns", []):
                    logger.info(f"    ➕ {col['name']}: {col['type']}")
                for col in changes.get("removed_columns", []):
                    logger.info(f"    ➖ {col['name']}: {col['type']}")
                for col in changes.get("modified_columns", []):
                    logger.info(f"    ✏️  {col['name']}: {col['old_type']} → {col['new_type']}")

            return {"data": result}
        except TableNotFoundError as e:
            logger.error(f"Table not found: {str(e)}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except InvalidTableError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except TableCreationError as e:
            logger.error(f"Update error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error updating table {table_name}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update table: {str(e)}",
            )

    @app.get("/api/v1/tables/{table_name}", status_code=status.HTTP_200_OK)
    async def get_table_info(table_name: str) -> dict:
        """Get information about an existing table."""
        try:
            logger.info(f"API: Fetching table {table_name}")
            result = await get_table_use_case.execute(table_name)
            return {"data": result}
        except TableNotFoundError as e:
            logger.error(f"Table not found: {str(e)}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return PrettyJSONResponse(
            status_code=500,
            content={"status": "error", "detail": "Internal server error"},
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "iceberg_creation_service.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )