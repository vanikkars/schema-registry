"""FastAPI HTTP router for schema registry endpoints (inbound adapter)."""

import logging
from fastapi import APIRouter, HTTPException, Query, Response, status
from typing import Optional

from registry_api.domain.models import DataContract
from registry_api.domain.exceptions import (
    SchemaRegistryError,
    SchemaNotFoundError,
    InvalidVersionError,
    VersionNotFoundError,
    RegistryNotFoundError,
    TableCreationError,
)
from registry_api.application.use_cases import (
    RegisterSchemaUseCase,
    ListSchemasUseCase,
    GetSchemaUseCase,
    GetSchemaVersionsUseCase,
    GetSchemaVersionUseCase,
    DeleteSchemaUseCase,
)
from .dto import build_schema_response

logger = logging.getLogger(__name__)


def create_router(
    register_schema_use_case: RegisterSchemaUseCase,
    list_schemas_use_case: ListSchemasUseCase,
    get_schema_use_case: GetSchemaUseCase,
    get_schema_versions_use_case: GetSchemaVersionsUseCase,
    get_schema_version_use_case: GetSchemaVersionUseCase,
    delete_schema_use_case: DeleteSchemaUseCase,
) -> APIRouter:
    """Create and configure the API router with all schema endpoints.

    Args:
        register_schema_use_case: Use case for registering schemas
        list_schemas_use_case: Use case for listing schemas
        get_schema_use_case: Use case for getting schema details
        get_schema_versions_use_case: Use case for getting schema versions
        get_schema_version_use_case: Use case for getting specific schema version
        delete_schema_use_case: Use case for deleting schemas

    Returns:
        Configured FastAPI APIRouter
    """
    router = APIRouter(prefix="/api/v1/schemas", tags=["schemas"])

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create_schema(contract: DataContract, response: Response) -> dict:
        """Create a new schema in AWS Glue Schema Registry and Iceberg table.

        Returns 201 Created with Location header pointing to created resource.
        """
        try:
            logger.info(f"Creating schema for contract: {contract.contract_id}")
            result = register_schema_use_case.execute(contract)
            logger.info(f"Successfully created schema: {contract.contract_id}")
            response.headers["Location"] = f"/api/v1/schemas/{contract.contract_id}"
            return {"data": result}
        except RegistryNotFoundError as e:
            logger.error(f"Registry not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )
        except TableCreationError as e:
            logger.error(f"Table creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except SchemaRegistryError as e:
            logger.error(f"Schema registry error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except ValueError as e:
            # Catch ValueError from compatibility violations
            logger.error(f"Schema validation failed for {contract.contract_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schema validation failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating schema {contract.contract_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schema: {str(e)}"
            )

    @router.get("")
    async def list_schemas_endpoint(
        limit: Optional[int] = Query(20, ge=1, le=100),
        offset: Optional[int] = Query(0, ge=0),
    ) -> dict:
        """List all schemas in the registry with pagination support."""
        try:
            result = list_schemas_use_case.execute(limit=limit, offset=offset)
            return {"data": result["schemas"], "meta": {
                "total": result["total"],
                "count": result["count"],
                "limit": result["limit"],
                "offset": result["offset"],
            }}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list schemas",
            )

    @router.get("/{schema_name}")
    async def get_schema_endpoint(schema_name: str) -> dict:
        """Get details of a specific schema by name."""
        try:
            result = get_schema_use_case.execute(schema_name)
            return {"data": result}
        except SchemaNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        except SchemaRegistryError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get schema",
            )

    @router.get("/{schema_name}/versions")
    async def get_schema_versions_endpoint(schema_name: str) -> dict:
        """Get version information for a specific schema."""
        try:
            result = get_schema_versions_use_case.execute(schema_name)
            return {"data": result}
        except SchemaNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        except SchemaRegistryError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get schema versions",
            )

    @router.get("/{schema_name}/versions/{version}")
    async def get_schema_version_endpoint(schema_name: str, version: str) -> dict:
        """Get a specific version of a schema.

        Note: AWS Glue Schema Registry tracks only the latest version.
        This endpoint returns the current schema if version matches latest.
        """
        try:
            result = get_schema_version_use_case.execute(schema_name, version)
            return {"data": result}
        except SchemaNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        except InvalidVersionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            )
        except VersionNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        except SchemaRegistryError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get schema version",
            )

    @router.delete("/{schema_name}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_schema_endpoint(schema_name: str) -> None:
        """Delete a schema from the registry.

        Note: AWS Glue Schema Registry doesn't support deletion via API.
        This endpoint is a placeholder for future implementation.
        """
        try:
            delete_schema_use_case.execute(schema_name)
            return None
        except SchemaNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        except SchemaRegistryError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete schema",
            )

    return router
