"""AWS Glue adapter for Iceberg table operations."""

import os
import boto3
import logging
from typing import Optional

from iceberg_creation_service.exceptions import TableCreationError
from iceberg_creation_service.models import CreateTableRequest

logger = logging.getLogger(__name__)


class GlueIcebergTableAdapter:
    """Adapter for AWS Glue Iceberg table operations."""

    def __init__(self, region: str = None):
        """Initialize the adapter.

        Args:
            region: AWS region (defaults to AWS_DEFAULT_REGION or us-east-1)
        """
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.glue = boto3.client("glue", region_name=self.region)
        self.sts = boto3.client("sts", region_name=self.region)

    def create_table(
        self,
        contract: CreateTableRequest,
        database_name: str = "iceberg_tables",
        s3_location: str = None,
    ) -> dict:
        """Create an Iceberg table from a data contract.

        Args:
            contract: The data contract defining the table schema
            database_name: Glue database name
            s3_location: S3 location for table data (auto-generated if None)

        Returns:
            Table creation response with status and details

        Raises:
            TableCreationError: If table creation fails
        """
        table_name = contract.contract_id.replace("-", "_").lower()

        # Generate S3 location if not provided
        if not s3_location:
            try:
                account_id = self.sts.get_caller_identity()["Account"]
            except Exception as e:
                raise TableCreationError(
                    f"Failed to get AWS account ID: {str(e)}"
                )
            s3_location = (
                f"s3://iceberg-data-{account_id}-{self.region}/{database_name}/{table_name}"
            )

        # Convert contract columns to Glue StorageDescriptor format
        columns = []
        for col in contract.columns:
            glue_type = self._map_type_to_glue(col.data_type)
            columns.append(
                {
                    "Name": col.name,
                    "Type": glue_type,
                    "Comment": col.description or "",
                }
            )

        try:
            # Create database if not exists
            try:
                self.glue.create_database(
                    DatabaseInput={"Name": database_name}
                )
            except self.glue.exceptions.AlreadyExistsException:
                pass

            # Create the table
            self.glue.create_table(
                DatabaseName=database_name,
                TableInput={
                    "Name": table_name,
                    "Description": contract.description
                    or f"Iceberg table for {contract.name}",
                    "StorageDescriptor": {
                        "Columns": columns,
                        "Location": s3_location,
                        "InputFormat": "org.apache.iceberg.mr.hive.IcebergInputFormat",
                        "OutputFormat": "org.apache.iceberg.mr.hive.IcebergOutputFormat",
                        "SerdeInfo": {
                            "SerializationLibrary": "org.apache.iceberg.serde.IcebergSerDe",
                        },
                    },
                    "PartitionKeys": [],
                    "TableType": "EXTERNAL_TABLE",
                    "Parameters": {
                        "EXTERNAL": "TRUE",
                        "table_type": "ICEBERG",
                        "iceberg_table_version": str(contract.version),
                        "data_owner": contract.metadata.data_owner
                        if contract.metadata
                        else "Unknown",
                        "data_steward": contract.metadata.data_steward
                        if contract.metadata
                        else "Unknown",
                    },
                },
            )
            logger.info(f"Created new Iceberg table: {table_name}")
            return {
                "status": "created",
                "table_name": table_name,
                "database_name": database_name,
                "s3_location": s3_location,
                "message": f"Iceberg table '{table_name}' created successfully",
            }

        except self.glue.exceptions.AlreadyExistsException:
            logger.info(f"Table already exists: {table_name}")
            return {
                "status": "exists",
                "table_name": table_name,
                "database_name": database_name,
                "s3_location": s3_location,
                "message": f"Iceberg table '{table_name}' already exists",
            }
        except Exception as e:
            raise TableCreationError(f"Failed to create table {table_name}: {str(e)}")

    def update_table_schema(
        self,
        contract: CreateTableRequest,
        database_name: str = "iceberg_tables",
    ) -> dict:
        """Update Iceberg table schema when contract evolves."""
        table_name = contract.contract_id.replace("-", "_").lower()

        try:
            current_table = self.glue.get_table(
                DatabaseName=database_name, Name=table_name
            )
            current_columns = {
                col["Name"]: col["Type"]
                for col in current_table["Table"]["StorageDescriptor"]["Columns"]
            }
        except self.glue.exceptions.EntityNotFoundException:
            raise TableCreationError(
                f"Table {table_name} not found in database {database_name}"
            )
        except Exception as e:
            raise TableCreationError(
                f"Failed to get current table schema: {str(e)}"
            )

        # Build new columns and detect changes
        new_columns = []
        changes = []
        warnings = []

        for col in contract.columns:
            glue_type = self._map_type_to_glue(col.data_type)
            new_columns.append(
                {
                    "Name": col.name,
                    "Type": glue_type,
                    "Comment": col.description or "",
                }
            )

        new_col_names = {col["Name"] for col in new_columns}
        current_col_names = set(current_columns.keys())

        # Detect changes
        added = new_col_names - current_col_names
        if added:
            for col_name in added:
                col = next(c for c in new_columns if c["Name"] == col_name)
                changes.append(f"Added column: {col_name} ({col['Type']})")

        removed = current_col_names - new_col_names
        if removed:
            for col_name in removed:
                warnings.append(f"Removed column: {col_name} (data will be lost)")

        # Update table
        try:
            self.glue.update_table(
                DatabaseName=database_name,
                TableInput={
                    "Name": table_name,
                    "Description": current_table["Table"]["Description"],
                    "StorageDescriptor": {
                        **current_table["Table"]["StorageDescriptor"],
                        "Columns": new_columns,
                    },
                    "PartitionKeys": current_table["Table"].get("PartitionKeys", []),
                    "TableType": current_table["Table"]["TableType"],
                    "Parameters": {
                        **current_table["Table"].get("Parameters", {}),
                        "iceberg_table_version": str(contract.version),
                    },
                },
            )

            return {
                "status": "updated",
                "table_name": table_name,
                "database_name": database_name,
                "changes": changes,
                "warnings": warnings,
                "message": "Table schema updated successfully",
            }

        except Exception as e:
            raise TableCreationError(f"Failed to update table schema: {str(e)}")

    def get_table_info(self, table_name: str, database_name: str = "iceberg_tables") -> dict:
        """Get information about an existing table."""
        try:
            table = self.glue.get_table(DatabaseName=database_name, Name=table_name)
            return {
                "table_name": table["Table"]["Name"],
                "database_name": database_name,
                "columns": table["Table"]["StorageDescriptor"]["Columns"],
                "location": table["Table"]["StorageDescriptor"]["Location"],
            }
        except Exception as e:
            raise TableCreationError(f"Failed to get table info: {str(e)}")

    @staticmethod
    def _map_type_to_glue(avro_type: str) -> str:
        """Map AVRO type to Glue type."""
        type_mapping = {
            "string": "string",
            "int": "int",
            "long": "bigint",
            "float": "float",
            "double": "double",
            "boolean": "boolean",
            "bytes": "binary",
            "date": "date",
            "timestamp": "timestamp",
        }
        return type_mapping.get(avro_type.lower(), "string")