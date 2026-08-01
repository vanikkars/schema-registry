"""Repository implementations - Data access layer."""

import logging
import boto3
from typing import Optional
from datetime import datetime

from iceberg_creation_service.domain.entities import IcebergTable
from iceberg_creation_service.domain.repositories import IcebergTableRepository
from iceberg_creation_service.domain.value_objects import TableName, DatabaseName
from iceberg_creation_service.domain.exceptions import (
    TableCreationError,
    TableNotFoundError,
)

logger = logging.getLogger(__name__)


class AwsGlueIcebergTableRepository(IcebergTableRepository):
    """
    AWS Glue implementation of IcebergTableRepository.

    Persists Iceberg tables to AWS Glue using boto3.
    """

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.glue = boto3.client("glue", region_name=region)
        self.sts = boto3.client("sts", region_name=region)

    async def save(self, table: IcebergTable) -> None:
        """Create a new Iceberg table in AWS Glue."""
        try:
            logger.debug(f"Saving table to Glue: {table.table_name}")

            # Generate S3 location if not provided
            if not table.s3_location:
                table.s3_location = await self._generate_s3_location(table)

            # Convert columns to Glue format
            columns = [col.to_glue_format() for col in table.columns]

            # Create table in Glue
            self.glue.create_table(
                DatabaseName=str(table.database_name),
                TableInput={
                    "Name": str(table.table_name),
                    "Description": table.description or f"Iceberg table for {table.contract_id}",
                    "StorageDescriptor": {
                        "Columns": columns,
                        "Location": str(table.s3_location),
                        "InputFormat": "org.apache.iceberg.mr.hive.IcebergInputFormat",
                        "OutputFormat": "org.apache.iceberg.mr.hive.IcebergOutputFormat",
                        "SerdeInfo": {
                            "SerializationLibrary": "org.apache.iceberg.serde.IcebergSerDe",
                        },
                    },
                    "PartitionKeys": [],
                    "TableType": "EXTERNAL_TABLE",
                    "Parameters": self._build_table_parameters(table),
                },
            )

            logger.info(f"Table saved to Glue: {table.table_name}")

        except self.glue.exceptions.AlreadyExistsException:
            logger.debug(f"Table already exists in Glue: {table.table_name}")
        except Exception as e:
            logger.error(f"Failed to save table to Glue: {str(e)}")
            raise TableCreationError(f"Failed to create table in Glue: {str(e)}")

    async def get_by_name(self, table_name: TableName) -> Optional[IcebergTable]:
        """Retrieve a table from AWS Glue by name."""
        try:
            logger.debug(f"Fetching table from Glue: {table_name}")

            # For now, return None as we're not storing full table state
            # In a real implementation, this would reconstruct from Glue metadata
            return None

        except self.glue.exceptions.EntityNotFoundException:
            return None
        except Exception as e:
            logger.error(f"Failed to get table from Glue: {str(e)}")
            raise TableNotFoundError(str(e))

    async def exists(self, table_name: TableName) -> bool:
        """Check if a table exists in AWS Glue."""
        try:
            logger.debug(f"Checking if table exists: {table_name}")

            # Get default database name
            database_name = "iceberg_tables"

            self.glue.get_table(
                DatabaseName=database_name,
                Name=str(table_name),
            )

            return True

        except self.glue.exceptions.EntityNotFoundException:
            return False
        except Exception as e:
            logger.error(f"Error checking table existence: {str(e)}")
            raise TableCreationError(str(e))

    async def update(self, table: IcebergTable) -> None:
        """Update an existing table's schema in AWS Glue."""
        try:
            logger.debug(f"Updating table in Glue: {table.table_name}")

            # Get current table
            response = self.glue.get_table(
                DatabaseName=str(table.database_name),
                Name=str(table.table_name),
            )

            current_table = response["Table"]

            # Convert updated columns to Glue format
            columns = [col.to_glue_format() for col in table.columns]

            # Update table
            self.glue.update_table(
                DatabaseName=str(table.database_name),
                TableInput={
                    "Name": str(table.table_name),
                    "Description": current_table.get("Description", ""),
                    "StorageDescriptor": {
                        **current_table["StorageDescriptor"],
                        "Columns": columns,
                    },
                    "PartitionKeys": current_table.get("PartitionKeys", []),
                    "TableType": current_table.get("TableType", "EXTERNAL_TABLE"),
                    "Parameters": {
                        **current_table.get("Parameters", {}),
                        "iceberg_table_version": str(table.version),
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                },
            )

            logger.info(f"Table updated in Glue: {table.table_name}")

        except self.glue.exceptions.EntityNotFoundException:
            raise TableNotFoundError(f"Table not found: {table.table_name}")
        except Exception as e:
            logger.error(f"Failed to update table in Glue: {str(e)}")
            raise TableCreationError(f"Failed to update table schema: {str(e)}")

    async def create_database_if_not_exists(self, database_name: str) -> None:
        """Create database if it doesn't exist."""
        try:
            logger.debug(f"Ensuring database exists: {database_name}")

            self.glue.create_database(
                DatabaseInput={"Name": database_name}
            )

            logger.info(f"Database created: {database_name}")

        except self.glue.exceptions.AlreadyExistsException:
            logger.debug(f"Database already exists: {database_name}")
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            raise TableCreationError(f"Failed to create database: {str(e)}")

    async def _generate_s3_location(self, table: IcebergTable) -> "S3Location":
        """Generate S3 location for the table."""
        try:
            account_id = self.sts.get_caller_identity()["Account"]
            location = f"s3://iceberg-data-{account_id}-{self.region}/{table.database_name}/{table.table_name}"
            from iceberg_creation_service.domain.value_objects import S3Location
            return S3Location(location)
        except Exception as e:
            logger.error(f"Failed to generate S3 location: {str(e)}")
            raise TableCreationError(f"Failed to generate S3 location: {str(e)}")

    def _build_table_parameters(self, table: IcebergTable) -> dict:
        """Build Glue table parameters from table entity."""
        params = {
            "EXTERNAL": "TRUE",
            "table_type": "ICEBERG",
            "iceberg_table_version": str(table.version),
            "created_at": table.created_at.isoformat(),
        }

        # Add metadata
        metadata_params = table.metadata.to_glue_parameters()
        params.update(metadata_params)

        return params