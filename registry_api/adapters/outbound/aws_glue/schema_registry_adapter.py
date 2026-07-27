"""AWS Glue Schema Registry adapter (implements SchemaRegistryPort)."""

import os
import boto3
from registry_api.application.ports import SchemaRegistryPort
from registry_api.domain.models import DataContract
from registry_api.domain.exceptions import RegistryNotFoundError
from .mappers import contract_to_avro, map_type_to_avro


class GlueSchemaRegistryAdapter(SchemaRegistryPort):
    """Adapter for AWS Glue Schema Registry operations using boto3."""

    def __init__(
        self,
        registry_name: str = None,
        region: str = None,
    ):
        """Initialize the adapter.

        Args:
            registry_name: Name of the Glue Schema Registry (defaults to env var TF_VAR_registry_name)
            region: AWS region (defaults to AWS_DEFAULT_REGION env var or us-east-1)
        """
        self.registry_name = registry_name or os.getenv(
            "TF_VAR_registry_name", "schema-registry"
        )
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.glue = boto3.client("glue", region_name=self.region)

    def register_schema(
        self,
        contract: DataContract,
        data_format: str = "AVRO",
        compatibility: str = "BACKWARD",
    ) -> str:
        """Register a data contract as a schema in the registry.

        Args:
            contract: The data contract to register
            data_format: Schema format (AVRO, PROTOBUF, JSON)
            compatibility: Compatibility mode (BACKWARD, FORWARD, BOTH, NONE, DISABLED)

        Returns:
            Schema ARN

        Raises:
            RegistryNotFoundError: If the registry does not exist
            ValueError: If schema registration fails for other reasons
        """
        schema_name = contract.contract_id
        description = contract.description or f"Schema for {schema_name}"

        # Convert contract to AVRO schema
        schema_definition = contract_to_avro(contract)

        try:
            # Check if registry exists
            registry = self.glue.get_registry(
                RegistryId={"RegistryName": self.registry_name}
            )
            registry_arn = registry["RegistryArn"]
        except self.glue.exceptions.EntityNotFoundException:
            raise RegistryNotFoundError(self.registry_name)

        # Build tags from metadata
        tags = {
            "ManagedBy": "python-api",
            "Source": "data-contract",
            "ContractVersion": contract.version,
        }
        if contract.metadata:
            tags.update(
                {
                    "DataOwner": contract.metadata.data_owner,
                    "DataOwnerEmail": contract.metadata.data_owner_email,
                    "DataSteward": contract.metadata.data_steward,
                    "DataStewardEmail": contract.metadata.data_steward_email,
                    "SLAUptimePercentage": str(
                        contract.metadata.sla_uptime_percentage
                    ),
                    "SLAMaxLatencyMs": str(contract.metadata.sla_max_latency_ms),
                }
            )

        try:
            # Try to get existing schema
            existing = self.glue.get_schema(
                SchemaId={
                    "RegistryName": self.registry_name,
                    "SchemaName": schema_name,
                }
            )
            # Schema exists - just return its ARN
            response = existing
        except self.glue.exceptions.EntityNotFoundException:
            # Create new schema
            response = self.glue.create_schema(
                RegistryId={"RegistryName": self.registry_name},
                SchemaName=schema_name,
                DataFormat=data_format,
                Compatibility=compatibility,
                Description=description,
                SchemaDefinition=schema_definition,
                Tags=tags,
            )

        return response.get("SchemaArn", "")

    def get_schema(self, schema_name: str) -> dict:
        """Get details of a schema by name.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details dict, or None if not found
        """
        try:
            response = self.glue.get_schema(
                SchemaId={
                    "RegistryName": self.registry_name,
                    "SchemaName": schema_name,
                }
            )
            return response
        except self.glue.exceptions.EntityNotFoundException:
            return None

    def list_schemas(self) -> list:
        """List all schemas in the registry.

        Returns:
            List of schema dicts
        """
        try:
            response = self.glue.list_schemas(
                RegistryId={"RegistryName": self.registry_name}
            )
            return response.get("Schemas", [])
        except self.glue.exceptions.EntityNotFoundException:
            return []

    def get_schema_versions(self, schema_name: str) -> dict:
        """Get version information for a schema.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details including version information, or None if not found
        """
        try:
            response = self.glue.get_schema(
                SchemaId={
                    "RegistryName": self.registry_name,
                    "SchemaName": schema_name,
                }
            )
            # Extract version info from schema details
            return {
                "schema_name": schema_name,
                "latest_version": response.get("LatestSchemaVersion", 0),
                "next_version": response.get("NextSchemaVersion", 0),
                "checkpoint": response.get("SchemaCheckpoint", ""),
                "status": response.get("SchemaStatus", "AVAILABLE"),
                "created_time": response.get("CreatedTime"),
                "updated_time": response.get("UpdatedTime"),
                "arn": response.get("SchemaArn"),
                "description": response.get("Description", ""),
            }
        except Exception:
            return None
