"""HTTP router for Iceberg table operations."""

import logging
from fastapi import APIRouter, HTTPException, status

from iceberg_creation_service.models import CreateTableRequest, TableCreationResponse
from iceberg_creation_service.adapters import GlueIcebergTableAdapter
from iceberg_creation_service.exceptions import TableCreationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tables", tags=["tables"])

table_adapter = GlueIcebergTableAdapter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_table(request: CreateTableRequest) -> dict:
    """Create an Iceberg table from a data contract."""
    try:
        logger.info(f"Creating table for contract: {request.name}")

        if not request.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract must have at least one column",
            )

        result = table_adapter.create_table(
            contract=request,
            database_name=request.database_name or "iceberg_tables",
        )

        logger.info(f"Table created successfully: {result['table_name']}")

        return {
            "data": TableCreationResponse(
                status=result["status"],
                table_name=result["table_name"],
                database_name=result["database_name"],
                s3_location=result.get("s3_location"),
                message=result.get("message", "Table created successfully"),
                warnings=[],
                errors=[],
            ).model_dump()
        }

    except TableCreationError as e:
        logger.error(f"Table creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Table creation failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during table creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/{table_name}/schema", status_code=status.HTTP_200_OK)
async def update_table_schema(table_name: str, request: CreateTableRequest) -> dict:
    """Update an existing Iceberg table schema."""
    try:
        logger.info(f"Updating table schema: {table_name}")

        result = table_adapter.update_table_schema(
            contract=request,
            database_name=request.database_name or "iceberg_tables",
        )

        logger.info(f"Table schema updated: {table_name}")

        return {
            "data": {
                "status": result.get("status", "updated"),
                "table_name": result["table_name"],
                "changes": result.get("changes", []),
                "warnings": result.get("warnings", []),
                "message": result.get("message", "Table schema updated"),
            }
        }

    except TableCreationError as e:
        logger.error(f"Schema update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schema update failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during schema update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{table_name}", status_code=status.HTTP_200_OK)
async def get_table_info(table_name: str) -> dict:
    """Get information about an existing Iceberg table."""
    try:
        result = table_adapter.get_table_info(table_name)
        return {"data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table not found: {str(e)}",
        )