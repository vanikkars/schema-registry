"""HTTP routes - API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status

from iceberg_creation_service.application.dto import CreateTableInputDto, UpdateTableSchemaInputDto
from iceberg_creation_service.application.use_cases import (
    CreateTableUseCase,
    UpdateTableSchemaUseCase,
    GetTableInfoUseCase,
)
from iceberg_creation_service.domain.exceptions import (
    DomainException,
    TableNotFoundError,
    InvalidTableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tables", tags=["tables"])


def create_routes(
    create_table_use_case: CreateTableUseCase,
    update_table_use_case: UpdateTableSchemaUseCase,
    get_table_use_case: GetTableInfoUseCase,
) -> APIRouter:
    """Create API routes with injected use cases."""

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create_table(request: CreateTableInputDto) -> dict:
        """
        Create an Iceberg table from a data contract.

        Returns 201 Created with table details.
        """
        try:
            logger.info(f"API: Creating table for contract {request.contract_id}")

            result = await create_table_use_case.execute(request)

            return {
                "data": result.to_dict()
            }

        except InvalidTableError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except DomainException as e:
            logger.error(f"Domain error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @router.post("/{table_name}/schema", status_code=status.HTTP_200_OK)
    async def update_table_schema(
        table_name: str, request: UpdateTableSchemaInputDto
    ) -> dict:
        """Update an existing table's schema."""
        try:
            logger.info(f"API: Updating schema for table {table_name}")

            result = await update_table_use_case.execute(request)

            return {
                "data": result.to_dict()
            }

        except TableNotFoundError as e:
            logger.error(f"Table not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except InvalidTableError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except DomainException as e:
            logger.error(f"Domain error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @router.get("/{table_name}", status_code=status.HTTP_200_OK)
    async def get_table_info(table_name: str) -> dict:
        """Get information about an existing table."""
        try:
            logger.info(f"API: Fetching info for table {table_name}")

            result = await get_table_use_case.execute(table_name)

            return {
                "data": result.to_dict()
            }

        except TableNotFoundError as e:
            logger.error(f"Table not found: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return router