"""AWS Glue Schema Registry adapter (implements SchemaRegistryPort)."""

import os
import boto3
import logging
from registry_api.application.ports import SchemaRegistryPort
from registry_api.domain.models import DataContract
from registry_api.domain.exceptions import RegistryNotFoundError
from .mappers import contract_to_avro, map_type_to_avro

logger = logging.getLogger(__name__)


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
        """Get version information for a schema, including the schema definition.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details including version information, schema definition, and metadata, or None if not found
        """
        try:
            schema_response = self.glue.get_schema(
                SchemaId={
                    "RegistryName": self.registry_name,
                    "SchemaName": schema_name,
                }
            )

            # Get the latest schema version to retrieve the actual schema definition
            latest_version = schema_response.get("LatestSchemaVersion", 0)
            schema_def = None

            if latest_version > 0:
                try:
                    version_response = self.glue.get_schema_version(
                        SchemaId={
                            "RegistryName": self.registry_name,
                            "SchemaName": schema_name,
                        },
                        SchemaVersionNumber={"LatestVersion": True},
                    )
                    schema_def = version_response.get("SchemaDefinition", "")
                except Exception as e:
                    logger.warning(f"Could not fetch schema definition for {schema_name}: {e}")
                    schema_def = None

            # Parse schema definition if available (for AVRO format)
            schema_content = None
            if schema_def:
                import json
                try:
                    schema_content = json.loads(schema_def)
                except Exception:
                    schema_content = schema_def

            # Extract metadata from tags (need separate API call)
            tags = {}
            try:
                schema_arn = schema_response.get("SchemaArn", "")
                if schema_arn:
                    tags_response = self.glue.get_tags(ResourceArn=schema_arn)
                    tags = tags_response.get("Tags", {})
            except Exception as e:
                logger.warning(f"Could not fetch tags for {schema_name}: {e}")

            metadata = {
                "data_owner": tags.get("DataOwner"),
                "data_owner_email": tags.get("DataOwnerEmail"),
                "data_steward": tags.get("DataSteward"),
                "data_steward_email": tags.get("DataStewardEmail"),
                "sla_uptime_percentage": self._parse_float(tags.get("SLAUptimePercentage")),
                "sla_max_latency_ms": self._parse_int(tags.get("SLAMaxLatencyMs")),
                "contract_version": tags.get("ContractVersion"),
                "managed_by": tags.get("ManagedBy"),
                "source": tags.get("Source"),
            }

            # Extract version info from schema details
            return {
                "schema_name": schema_name,
                "latest_version": latest_version,
                "next_version": schema_response.get("NextSchemaVersion", 0),
                "checkpoint": schema_response.get("SchemaCheckpoint", ""),
                "status": schema_response.get("SchemaStatus", "AVAILABLE"),
                "created_time": schema_response.get("CreatedTime"),
                "updated_time": schema_response.get("UpdatedTime"),
                "arn": schema_response.get("SchemaArn"),
                "description": schema_response.get("Description", ""),
                "data_format": schema_response.get("DataFormat", "AVRO"),
                "compatibility": schema_response.get("Compatibility", "BACKWARD"),
                "metadata": metadata,
                "schema": schema_content,
            }
        except Exception:
            return None

    def _parse_float(self, value: str) -> float:
        """Parse string to float, return None if invalid."""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: str) -> int:
        """Parse string to int, return None if invalid."""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
