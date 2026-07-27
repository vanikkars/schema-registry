"""AWS Glue Iceberg table catalog adapter (implements TableCatalogPort)."""

import os
import boto3
from registry_api.application.ports import TableCatalogPort
from registry_api.domain.models import DataContract
from registry_api.domain.exceptions import TableCreationError
from .mappers import map_type_to_glue


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
            # Create or update the table
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
            return {
                "status": "created",
                "table_name": table_name,
                "database_name": database_name,
                "s3_location": s3_location,
                "message": f"Iceberg table '{table_name}' created successfully",
            }
        except self.glue.exceptions.AlreadyExistsException:
            # Table already exists - return its location
            return {
                "status": "exists",
                "table_name": table_name,
                "database_name": database_name,
                "s3_location": s3_location,
                "message": f"Iceberg table '{table_name}' already exists",
            }
        except Exception as e:
            raise TableCreationError(table_name, str(e))
