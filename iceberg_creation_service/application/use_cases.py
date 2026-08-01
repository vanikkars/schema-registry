"""Use Cases - Application business logic orchestration."""

import logging
from typing import Optional

from iceberg_creation_service.application.dto import (
    CreateTableInputDto,
    CreateTableOutputDto,
    UpdateTableSchemaInputDto,
    UpdateTableSchemaOutputDto,
    GetTableInfoOutputDto,
)
from iceberg_creation_service.domain.entities import IcebergTable, SchemaEvolution
from iceberg_creation_service.domain.repositories import IcebergTableRepository
from iceberg_creation_service.domain.value_objects import (
    TableName,
    ContractId,
    Version,
    Column,
    DatabaseName,
    S3Location,
    TableMetadata,
    TableStatus,
    DataType,
)
from iceberg_creation_service.domain.exceptions import (
    TableCreationError,
    TableNotFoundError,
    InvalidTableError,
    InvalidDataTypeError,
    DuplicateTableError,
)

logger = logging.getLogger(__name__)


class CreateTableUseCase:
    """
    Use case for creating an Iceberg table.

    Orchestrates the creation of a new Iceberg table from a data contract.
    """

    def __init__(self, repository: IcebergTableRepository):
        self.repository = repository

    async def execute(self, input_dto: CreateTableInputDto) -> CreateTableOutputDto:
        """
        Execute table creation.

        Args:
            input_dto: Create table input DTO

        Returns:
            CreateTableOutputDto with creation result

        Raises:
            InvalidTableError: If input validation fails
            DuplicateTableError: If table already exists
            TableCreationError: If table creation fails
        """
        logger.info(f"Creating Iceberg table for contract: {input_dto.name}")

        try:
            # Convert input DTO to domain objects
            table = self._build_table_from_input(input_dto)

            # Validate business rules
            table.validate()

            # Ensure database exists
            await self.repository.create_database_if_not_exists(
                str(table.database_name)
            )

            # Check if table already exists
            if await self.repository.exists(table.table_name):
                logger.info(f"Table already exists: {table.table_name}")
                table.mark_as_exists()
                await self.repository.save(table)
                return CreateTableOutputDto(
                    status=TableStatus.EXISTS,
                    table_name=str(table.table_name),
                    database_name=str(table.database_name),
                    s3_location=str(table.s3_location) if table.s3_location else None,
                    message=f"Iceberg table '{table.table_name}' already exists",
                )

            # Save the new table
            await self.repository.save(table)

            logger.info(f"Table created successfully: {table.table_name}")

            return CreateTableOutputDto(
                status=TableStatus.CREATED,
                table_name=str(table.table_name),
                database_name=str(table.database_name),
                s3_location=str(table.s3_location) if table.s3_location else None,
                message=f"Iceberg table '{table.table_name}' created successfully",
            )

        except (InvalidTableError, InvalidDataTypeError, DuplicateTableError) as e:
            logger.error(f"Validation error during table creation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during table creation: {str(e)}")
            raise TableCreationError(str(e))

    def _build_table_from_input(self, input_dto: CreateTableInputDto) -> IcebergTable:
        """Build domain table entity from input DTO."""
        try:
            # Create value objects
            table_name = TableName(input_dto.name.lower()).normalize()
            contract_id = ContractId(input_dto.contract_id)
            version = Version.from_int(input_dto.version)

            # Convert columns
            columns = []
            for col_dto in input_dto.columns:
                try:
                    data_type = DataType[col_dto.data_type.upper()]
                except KeyError:
                    raise InvalidDataTypeError(
                        f"Unsupported data type: {col_dto.data_type}"
                    )
                columns.append(
                    Column(
                        name=col_dto.name,
                        data_type=data_type,
                        description=col_dto.description,
                    )
                )

            # Create metadata
            metadata = TableMetadata(
                data_owner=input_dto.data_owner,
                data_steward=input_dto.data_steward,
            )

            # Create database name
            database_name = (
                DatabaseName(input_dto.database_name)
                if input_dto.database_name
                else DatabaseName()
            )

            # Create or use provided S3 location
            s3_location = None
            if input_dto.s3_location:
                s3_location = S3Location(input_dto.s3_location)

            # Create table entity
            table = IcebergTable(
                table_name=table_name,
                contract_id=contract_id,
                version=version,
                columns=columns,
                database_name=database_name,
                s3_location=s3_location,
                metadata=metadata,
                description=input_dto.description,
            )

            return table

        except (ValueError, KeyError) as e:
            raise InvalidTableError(f"Failed to build table from input: {str(e)}")


class UpdateTableSchemaUseCase:
    """
    Use case for updating an Iceberg table schema.

    Handles schema evolution with change tracking and validation.
    """

    def __init__(self, repository: IcebergTableRepository):
        self.repository = repository

    async def execute(
        self, input_dto: UpdateTableSchemaInputDto
    ) -> UpdateTableSchemaOutputDto:
        """
        Execute schema update.

        Args:
            input_dto: Update schema input DTO

        Returns:
            UpdateTableSchemaOutputDto with update result

        Raises:
            TableNotFoundError: If table does not exist
            InvalidTableError: If update validation fails
            TableCreationError: If update fails
        """
        logger.info(f"Updating table schema for: {input_dto.name}")

        try:
            # Get existing table
            table_name = TableName(input_dto.name.lower()).normalize()
            table = await self.repository.get_by_name(table_name)

            if not table:
                raise TableNotFoundError(f"Table not found: {table_name}")

            # Build new columns
            new_columns = []
            for col_dto in input_dto.columns:
                try:
                    data_type = DataType[col_dto.data_type.upper()]
                except KeyError:
                    raise InvalidDataTypeError(
                        f"Unsupported data type: {col_dto.data_type}"
                    )
                new_columns.append(
                    Column(
                        name=col_dto.name,
                        data_type=data_type,
                        description=col_dto.description,
                    )
                )

            # Detect changes
            evolution = table.update_schema(new_columns)

            # Update version
            table.version = Version.from_int(input_dto.version)

            # Persist changes
            await self.repository.update(table)

            logger.info(
                f"Table schema updated: {table_name} "
                f"({len(evolution.added_columns)} added, "
                f"{len(evolution.removed_columns)} removed)"
            )

            return UpdateTableSchemaOutputDto(
                status=TableStatus.UPDATED,
                table_name=str(table.table_name),
                database_name=str(table.database_name),
                message=f"Table schema updated for '{table.table_name}'",
                changes=evolution.get_changes(),
                warnings=evolution.get_warnings(),
            )

        except (TableNotFoundError, InvalidTableError) as e:
            logger.error(f"Error during schema update: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during schema update: {str(e)}")
            raise TableCreationError(str(e))


class GetTableInfoUseCase:
    """Use case for retrieving table information."""

    def __init__(self, repository: IcebergTableRepository):
        self.repository = repository

    async def execute(self, table_name: str) -> GetTableInfoOutputDto:
        """
        Get table information.

        Args:
            table_name: The table name to retrieve

        Returns:
            GetTableInfoOutputDto with table details

        Raises:
            TableNotFoundError: If table does not exist
        """
        normalized_name = TableName(table_name).normalize()
        table = await self.repository.get_by_name(normalized_name)

        if not table:
            raise TableNotFoundError(f"Table not found: {normalized_name}")

        columns = [col.to_glue_format() for col in table.columns]

        return GetTableInfoOutputDto(
            table_name=str(table.table_name),
            database_name=str(table.database_name),
            columns=columns,
            location=str(table.s3_location) if table.s3_location else "unknown",
        )