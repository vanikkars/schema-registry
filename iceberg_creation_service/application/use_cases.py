"""Use cases - Application business logic."""

import logging
from typing import Optional

from iceberg_creation_service.domain.models import IcebergTable, DataType, Column, SchemaChange
from iceberg_creation_service.domain.exceptions import InvalidTableError, TableNotFoundError

logger = logging.getLogger(__name__)


class CreateTableUseCase:
    """Use case for creating an Iceberg table."""

    def __init__(self, repository):
        self.repository = repository

    async def execute(self, contract: dict) -> dict:
        """
        Create an Iceberg table from a data contract.

        Args:
            contract: Contract dict with table definition

        Returns:
            Result dict with status and table details
        """
        logger.info(f"Creating table for contract: {contract.get('name')}")

        try:
            # Build table from contract
            table = self._build_table_from_contract(contract)

            # Validate
            table.validate()

            # Ensure database exists
            await self.repository.create_database_if_not_exists(table.database_name)

            # Check if exists
            if await self.repository.exists(table.table_name):
                logger.info(f"Table already exists: {table.table_name}")
                return {
                    "status": "exists",
                    "table_name": table.table_name,
                    "database_name": table.database_name,
                    "s3_location": table.s3_location,
                    "message": f"Iceberg table '{table.table_name}' already exists",
                }

            # Save
            await self.repository.save(table)

            logger.info(f"Table created: {table.table_name}")
            return {
                "status": "created",
                "table_name": table.table_name,
                "database_name": table.database_name,
                "s3_location": table.s3_location,
                "message": f"Iceberg table '{table.table_name}' created successfully",
            }

        except InvalidTableError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise

    def _build_table_from_contract(self, contract: dict) -> IcebergTable:
        """Build table entity from contract."""
        try:
            # Convert columns
            columns = []
            for col_dict in contract.get("columns", []):
                try:
                    data_type = DataType[col_dict["data_type"].upper()]
                except (KeyError, ValueError):
                    raise InvalidTableError(f"Unsupported data type: {col_dict['data_type']}")

                columns.append(
                    Column(
                        name=col_dict["name"],
                        data_type=data_type,
                        description=col_dict.get("description"),
                    )
                )

            # Create table using contract_id as table name (consistent with registry_api)
            table = IcebergTable(
                table_name=contract.get("contract_id", "").replace("-", "_").lower(),
                contract_id=contract.get("contract_id"),
                version=contract.get("version", 1),
                columns=columns,
                database_name=contract.get("database_name", "iceberg_tables"),
                description=contract.get("description"),
                data_owner=contract.get("metadata", {}).get("data_owner"),
                data_steward=contract.get("metadata", {}).get("data_steward"),
                s3_location=contract.get("s3_location"),
            )

            return table

        except (KeyError, ValueError) as e:
            raise InvalidTableError(f"Invalid contract: {str(e)}")


class UpdateTableSchemaUseCase:
    """Use case for updating table schema."""

    def __init__(self, repository):
        self.repository = repository

    async def execute(self, table_name: str, contract: dict) -> dict:
        """
        Update table schema.

        Args:
            table_name: Table to update
            contract: Updated contract with new columns

        Returns:
            Result dict with changes and warnings
        """
        logger.info(f"Updating table schema: {table_name}")

        try:
            # Get existing table
            table = await self.repository.get_by_name(table_name)
            if not table:
                raise TableNotFoundError(f"Table not found: {table_name}")

            # Build new columns
            new_columns = []
            for col_dict in contract.get("columns", []):
                try:
                    data_type = DataType[col_dict["data_type"].upper()]
                except (KeyError, ValueError):
                    raise InvalidTableError(f"Unsupported data type: {col_dict['data_type']}")

                new_columns.append(
                    Column(
                        name=col_dict["name"],
                        data_type=data_type,
                        description=col_dict.get("description"),
                    )
                )

            # Detect changes
            old_col_names = {col.name: col for col in table.columns}
            new_col_names = {col.name: col for col in new_columns}

            added = [col for col in new_columns if col.name not in old_col_names]
            removed = [col for col in table.columns if col.name not in new_col_names]
            modified = [
                (old_col_names[col.name], col)
                for col in new_columns
                if col.name in old_col_names and old_col_names[col.name].data_type != col.data_type
            ]

            # Create change object
            changes = SchemaChange(
                added_columns=added,
                removed_columns=removed,
                modified_columns=modified,
            )

            # Update table
            table.columns = new_columns
            table.version = contract.get("version", table.version)
            await self.repository.update(table)

            logger.info(f"Table schema updated: {table_name}")
            return {
                "status": "updated",
                "table_name": table_name,
                "database_name": table.database_name,
                "message": f"Table schema updated for '{table_name}'",
                "changes": changes.get_changes(),
                "warnings": changes.get_warnings(),
            }

        except (TableNotFoundError, InvalidTableError) as e:
            logger.error(f"Error updating schema: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating schema: {str(e)}")
            raise


class GetTableInfoUseCase:
    """Use case for getting table info."""

    def __init__(self, repository):
        self.repository = repository

    async def execute(self, table_name: str) -> dict:
        """Get table information."""
        table = await self.repository.get_by_name(table_name)
        if not table:
            raise TableNotFoundError(f"Table not found: {table_name}")

        return {
            "table_name": table.table_name,
            "database_name": table.database_name,
            "columns": table.to_glue_columns(),
            "location": table.s3_location or "unknown",
        }