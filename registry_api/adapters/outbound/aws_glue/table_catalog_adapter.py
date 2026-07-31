"""AWS Glue Iceberg table catalog adapter (implements TableCatalogPort)."""

import os
import boto3
import logging
from registry_api.application.ports import TableCatalogPort
from registry_api.domain.models import DataContract
from registry_api.domain.exceptions import TableCreationError
from .mappers import map_type_to_glue

logger = logging.getLogger(__name__)


class GlueIcebergTableAdapter(TableCatalogPort):
    """Adapter for AWS Glue Iceberg table operations using boto3."""

    def __init__(self, region: str = None):
        """Initialize the adapter.

        Args:
            region: AWS region (defaults to AWS_DEFAULT_REGION env var or us-east-1)
        """
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.glue = boto3.client("glue", region_name=self.region)
        self.sts = boto3.client("sts", region_name=self.region)

    def create_table(
        self,
        contract: DataContract,
        database_name: str = "iceberg_tables",
        s3_location: str = None,
    ) -> dict:
        """Create an Iceberg table from a data contract.

        Args:
            contract: The data contract defining the table schema
            database_name: Glue database name
            s3_location: S3 location for table data (auto-generated if None)

        Returns:
            Table creation response with 'status', 'table_name', 'database_name', 's3_location'

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
                    table_name, f"Failed to get AWS account ID: {str(e)}"
                )
            s3_location = (
                f"s3://iceberg-data-{account_id}-{self.region}/{database_name}/{table_name}"
            )

        # Convert contract columns to Glue StorageDescriptor format
        columns = []
        for col in contract.columns:
            glue_type = map_type_to_glue(col.data_type)
            columns.append(
                {
                    "Name": col.name,
                    "Type": glue_type,
                    "Comment": col.description or "",
                }
            )

        try:
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
                        "iceberg_table_version": contract.version,
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
            # Table already exists - this will be handled by caller (update_table_schema)
            logger.info(f"Table already exists: {table_name}, returning exists status")
            return {
                "status": "exists",
                "table_name": table_name,
                "database_name": database_name,
                "s3_location": s3_location,
                "message": f"Iceberg table '{table_name}' already exists",
            }
        except Exception as e:
            raise TableCreationError(table_name, str(e))

    def update_table_schema(
        self,
        contract: DataContract,
        database_name: str = "iceberg_tables",
    ) -> dict:
        """Update Iceberg table schema when contract evolves.

        Safe evolution:
        - Adding nullable columns (backward compatible)

        Risky changes (warnings):
        - Changing column types
        - Removing columns
        - Making non-nullable columns nullable

        Args:
            contract: The updated data contract
            database_name: Glue database name

        Returns:
            Update response with status, changes, warnings

        Raises:
            TableCreationError: If schema update fails
        """
        table_name = contract.contract_id.replace("-", "_").lower()

        try:
            # Get current table
            current_table = self.glue.get_table(
                DatabaseName=database_name, Name=table_name
            )
            current_columns = {
                col["Name"]: col["Type"]
                for col in current_table["Table"]["StorageDescriptor"]["Columns"]
            }
        except self.glue.exceptions.EntityNotFoundException:
            raise TableCreationError(
                table_name, f"Table {table_name} not found in database {database_name}"
            )
        except Exception as e:
            raise TableCreationError(
                table_name, f"Failed to get current table schema: {str(e)}"
            )

        # Build new columns
        new_columns = []
        changes = []
        warnings = []

        for col in contract.columns:
            glue_type = map_type_to_glue(col.data_type)
            new_columns.append(
                {
                    "Name": col.name,
                    "Type": glue_type,
                    "Comment": col.description or "",
                }
            )

        # Detect changes
        new_col_names = {col["Name"] for col in new_columns}
        current_col_names = set(current_columns.keys())

        # Added columns
        added = new_col_names - current_col_names
        if added:
            for col_name in added:
                col = next(c for c in new_columns if c["Name"] == col_name)
                changes.append(f"Added column: {col_name} ({col['Type']})")
                logger.info(f"Schema evolution: Added column {col_name}")

        # Removed columns (warning)
        removed = current_col_names - new_col_names
        if removed:
            for col_name in removed:
                warnings.append(f"Removed column: {col_name} (data will be lost)")
                logger.warning(f"Schema evolution: Removed column {col_name}")

        # Modified columns (warning)
        for col_name in current_col_names & new_col_names:
            new_type = next(
                (c["Type"] for c in new_columns if c["Name"] == col_name), None
            )
            current_type = current_columns[col_name]
            if new_type != current_type:
                warnings.append(
                    f"Modified column type: {col_name} ({current_type} → {new_type})"
                )
                logger.warning(
                    f"Schema evolution: Changed {col_name} type {current_type} → {new_type}"
                )

        # Update table with new schema
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
                        "iceberg_table_version": contract.version,
                    },
                },
            )

            result = {
                "status": "updated",
                "table_name": table_name,
                "database_name": database_name,
                "changes": changes,
                "warnings": warnings,
                "message": f"Iceberg table '{table_name}' schema updated",
            }

            if not changes and not warnings:
                result["message"] = "No schema changes detected"

            logger.info(f"Schema evolution completed for {table_name}: {changes}")
            return result

        except Exception as e:
            raise TableCreationError(
                table_name, f"Failed to update table schema: {str(e)}"
            )
