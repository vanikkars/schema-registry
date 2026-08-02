"""AWS Glue adapter for Iceberg table operations."""

import os
import boto3
import logging
from typing import Optional

from iceberg_creation_service.domain.models import IcebergTable
from iceberg_creation_service.domain.exceptions import TableCreationError, TableNotFoundError

logger = logging.getLogger(__name__)


class AwsGlueIcebergAdapter:
    """Adapter for AWS Glue Iceberg operations."""

    def __init__(self, region: str = None):
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.glue = boto3.client("glue", region_name=self.region)
        self.sts = boto3.client("sts", region_name=self.region)

    async def save(self, table: IcebergTable) -> None:
        """Create a new Iceberg table."""
        try:
            logger.debug(f"Creating table in Glue: {table.table_name}")

            # Generate S3 location if needed
            if not table.s3_location:
                account_id = self.sts.get_caller_identity()["Account"]
                table.s3_location = f"s3://iceberg-data-{account_id}-{self.region}/{table.database_name}/{table.table_name}"

            # Create table
            self.glue.create_table(
                DatabaseName=table.database_name,
                TableInput={
                    "Name": table.table_name,
                    "Description": table.description or f"Iceberg table for {table.contract_id}",
                    "StorageDescriptor": {
                        "Columns": table.to_glue_columns(),
                        "Location": table.s3_location,
                        "InputFormat": "org.apache.iceberg.mr.hive.IcebergInputFormat",
                        "OutputFormat": "org.apache.iceberg.mr.hive.IcebergOutputFormat",
                        "SerdeInfo": {
                            "SerializationLibrary": "org.apache.iceberg.serde.IcebergSerDe",
                        },
                    },
                    "PartitionKeys": [],
                    "TableType": "EXTERNAL_TABLE",
                    "Parameters": table.get_table_parameters(),
                },
            )
            logger.info(f"Table created in Glue: {table.table_name}")

        except self.glue.exceptions.AlreadyExistsException:
            logger.debug(f"Table already exists: {table.table_name}")
        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            raise TableCreationError(f"Failed to create table: {str(e)}")

    async def get_by_name(self, table_name: str, database_name: str = "iceberg_tables") -> Optional[IcebergTable]:
        """Get table from Glue and reconstruct as IcebergTable object."""
        try:
            response = self.glue.get_table(DatabaseName=database_name, Name=table_name)
            table_data = response["Table"]

            # Reconstruct columns from Glue format
            from iceberg_creation_service.domain.models import DataType, Column

            columns = []
            for col in table_data.get("StorageDescriptor", {}).get("Columns", []):
                try:
                    data_type = DataType[col["Type"].upper()]
                except (KeyError, ValueError):
                    logger.warning(f"Unknown data type {col['Type']}, skipping column {col['Name']}")
                    continue

                columns.append(Column(
                    name=col["Name"],
                    data_type=data_type,
                    description=col.get("Comment")
                ))

            # Extract metadata from table parameters
            params = table_data.get("Parameters", {})

            return IcebergTable(
                table_name=table_name,
                contract_id=params.get("contract_id", table_name),
                version=int(params.get("iceberg_table_version", 1)),
                columns=columns,
                database_name=database_name,
                description=table_data.get("Description"),
                data_owner=params.get("data_owner"),
                data_steward=params.get("data_steward"),
                s3_location=table_data.get("StorageDescriptor", {}).get("Location")
            )
        except self.glue.exceptions.EntityNotFoundException:
            return None
        except Exception as e:
            logger.error(f"Error retrieving table: {str(e)}")
            return None

    async def exists(self, table_name: str, database_name: str = "iceberg_tables") -> bool:
        """Check if table exists in Glue."""
        try:
            self.glue.get_table(DatabaseName=database_name, Name=table_name)
            return True
        except self.glue.exceptions.EntityNotFoundException:
            return False
        except Exception as e:
            logger.error(f"Error checking table existence: {str(e)}")
            raise TableCreationError(str(e))

    async def update(self, table: IcebergTable) -> None:
        """Update table schema."""
        try:
            response = self.glue.get_table(
                DatabaseName=table.database_name,
                Name=table.table_name,
            )
            current_table = response["Table"]

            self.glue.update_table(
                DatabaseName=table.database_name,
                TableInput={
                    "Name": table.table_name,
                    "Description": current_table.get("Description", ""),
                    "StorageDescriptor": {
                        **current_table["StorageDescriptor"],
                        "Columns": table.to_glue_columns(),
                    },
                    "PartitionKeys": current_table.get("PartitionKeys", []),
                    "TableType": current_table.get("TableType", "EXTERNAL_TABLE"),
                    "Parameters": {
                        **current_table.get("Parameters", {}),
                        "iceberg_table_version": str(table.version),
                    },
                },
            )
            logger.info(f"Table schema updated: {table.table_name}")

        except self.glue.exceptions.EntityNotFoundException:
            raise TableNotFoundError(f"Table not found: {table.table_name}")
        except Exception as e:
            logger.error(f"Failed to update table: {str(e)}")
            raise TableCreationError(f"Failed to update table: {str(e)}")

    async def create_database_if_not_exists(self, database_name: str) -> None:
        """Create database if needed."""
        try:
            self.glue.create_database(DatabaseInput={"Name": database_name})
            logger.info(f"Database created: {database_name}")
        except self.glue.exceptions.AlreadyExistsException:
            logger.debug(f"Database already exists: {database_name}")
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            raise TableCreationError(f"Failed to create database: {str(e)}")