"""Application use cases orchestrating domain logic and outbound ports."""

from typing import Optional
from registry_api.domain.models import DataContract
from registry_api.domain.exceptions import (
    SchemaNotFoundError,
    InvalidVersionError,
    VersionNotFoundError,
)
from registry_api.application.ports import SchemaRegistryPort, TableCatalogPort


class RegisterSchemaUseCase:
    """Use case for registering a new data contract as a schema."""

    def __init__(
        self,
        schema_registry: SchemaRegistryPort,
        table_catalog: TableCatalogPort,
    ):
        self.schema_registry = schema_registry
        self.table_catalog = table_catalog

    def execute(self, contract: DataContract) -> dict:
        """Register a schema in the registry and create an Iceberg table.

        Args:
            contract: Data contract to register

        Returns:
            Response dict with schema and table info

        Raises:
            SchemaRegistryError subclasses on domain/infrastructure errors
        """
        # Register schema in Glue Schema Registry
        schema_arn = self.schema_registry.register_schema(contract)
        schema_details = self.schema_registry.get_schema(contract.contract_id)

        # Create Iceberg table from schema
        table_info = self.table_catalog.create_table(contract)

        return {
            "schema": {
                "arn": schema_arn,
                "name": contract.contract_id,
                "version": contract.version,
                "description": schema_details.get("Description", "") if schema_details else "",
                "latest_version": schema_details.get("LatestSchemaVersion", 0)
                if schema_details
                else 0,
                "next_version": schema_details.get("NextSchemaVersion", 0)
                if schema_details
                else 0,
                "checkpoint": schema_details.get("SchemaCheckpoint", "")
                if schema_details
                else "",
                "status": schema_details.get("SchemaStatus", "AVAILABLE")
                if schema_details
                else "AVAILABLE",
                "data_format": schema_details.get("DataFormat", "AVRO")
                if schema_details
                else "AVRO",
                "compatibility": schema_details.get("Compatibility", "BACKWARD")
                if schema_details
                else "BACKWARD",
                "columns": [
                    {
                        "name": col.name,
                        "type": col.data_type,
                        "nullable": col.nullable,
                        "description": col.description,
                    }
                    for col in contract.columns
                ],
                "metadata": contract.metadata.model_dump()
                if contract.metadata
                else {},
                "created_at": str(schema_details.get("CreatedTime", ""))
                if schema_details
                else "",
                "updated_at": str(schema_details.get("UpdatedTime", ""))
                if schema_details
                else "",
            },
            "table": {
                "name": table_info["table_name"],
                "database": table_info["database_name"],
                "location": table_info["s3_location"],
                "status": table_info["status"],
            },
        }


class ListSchemasUseCase:
    """Use case for listing all schemas in the registry."""

    def __init__(self, schema_registry: SchemaRegistryPort):
        self.schema_registry = schema_registry

    def execute(self, limit: int = 20, offset: int = 0) -> dict:
        """List schemas with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Response dict with schemas and pagination metadata
        """
        schemas = self.schema_registry.list_schemas()
        total = len(schemas)
        paginated = schemas[offset : offset + limit]

        return {
            "schemas": paginated,
            "total": total,
            "count": len(paginated),
            "limit": limit,
            "offset": offset,
        }


class GetSchemaUseCase:
    """Use case for retrieving a specific schema's details including latest version metadata."""

    def __init__(self, schema_registry: SchemaRegistryPort):
        self.schema_registry = schema_registry

    def execute(self, schema_name: str) -> dict:
        """Get details of a specific schema with latest version metadata.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details dict with metadata fields

        Raises:
            SchemaNotFoundError: If schema does not exist
        """
        version_info = self.schema_registry.get_schema_versions(schema_name)

        if not version_info:
            raise SchemaNotFoundError(schema_name)

        return {
            "name": version_info.get("schema_name"),
            "arn": version_info.get("arn"),
            "description": version_info.get("description", ""),
            "status": version_info.get("status", "AVAILABLE"),
            "data_format": version_info.get("data_format", "AVRO"),
            "compatibility": version_info.get("compatibility", "BACKWARD"),
            "latest_version": version_info.get("latest_version", 0),
            "next_version": version_info.get("next_version", 0),
            "checkpoint": version_info.get("checkpoint", ""),
            "created_time": version_info.get("created_time"),
            "updated_time": version_info.get("updated_time"),
            "metadata": version_info.get("metadata", {}),
            "schema": version_info.get("schema"),
        }


class GetSchemaVersionsUseCase:
    """Use case for retrieving all version information for a schema including metadata."""

    def __init__(self, schema_registry: SchemaRegistryPort):
        self.schema_registry = schema_registry

    def execute(self, schema_name: str) -> dict:
        """Get all versions of a schema with metadata.

        Args:
            schema_name: Name of the schema

        Returns:
            Dict with schema info and list of all versions with their details and metadata

        Raises:
            SchemaNotFoundError: If schema does not exist
        """
        # Get latest version info for schema metadata
        latest_info = self.schema_registry.get_schema_versions(schema_name)

        if not latest_info:
            raise SchemaNotFoundError(schema_name)

        # Get all versions
        all_versions = self.schema_registry.list_all_schema_versions(schema_name)

        return {
            "schema_name": latest_info.get("schema_name"),
            "latest_version": latest_info.get("latest_version", 0),
            "next_version": latest_info.get("next_version", 0),
            "arn": latest_info.get("arn"),
            "description": latest_info.get("description", ""),
            "data_format": latest_info.get("data_format", "AVRO"),
            "compatibility": latest_info.get("compatibility", "BACKWARD"),
            "metadata": latest_info.get("metadata", {}),
            "versions": all_versions,
        }


class GetSchemaVersionUseCase:
    """Use case for retrieving a specific version of a schema."""

    def __init__(self, schema_registry: SchemaRegistryPort):
        self.schema_registry = schema_registry

    def execute(self, schema_name: str, version: str) -> dict:
        """Get a specific version of a schema with metadata.

        Args:
            schema_name: Name of the schema
            version: Version string

        Returns:
            Schema version details with full schema definition and metadata

        Raises:
            SchemaNotFoundError: If schema does not exist
            InvalidVersionError: If version format is invalid
            VersionNotFoundError: If specific version does not exist
        """
        version_info = self.schema_registry.get_schema_versions(schema_name)

        if not version_info:
            raise SchemaNotFoundError(schema_name)

        # Validate version format
        try:
            requested_version = int(version)
        except ValueError:
            raise InvalidVersionError(schema_name, version)

        # Check if requested version matches latest
        latest_version = version_info.get("latest_version", 0)
        if requested_version != latest_version:
            raise VersionNotFoundError(schema_name, version, latest_version)

        return {
            "schema_name": version_info.get("schema_name"),
            "version": latest_version,
            "arn": version_info.get("arn"),
            "description": version_info.get("description", ""),
            "status": version_info.get("status", "AVAILABLE"),
            "data_format": version_info.get("data_format", "AVRO"),
            "compatibility": version_info.get("compatibility", "BACKWARD"),
            "created_time": version_info.get("created_time"),
            "updated_time": version_info.get("updated_time"),
            "checkpoint": version_info.get("checkpoint", ""),
            "metadata": version_info.get("metadata", {}),
            "schema": version_info.get("schema"),
        }


class DeleteSchemaUseCase:
    """Use case for deleting a schema from the registry."""

    def __init__(self, schema_registry: SchemaRegistryPort):
        self.schema_registry = schema_registry

    def execute(self, schema_name: str) -> None:
        """Delete a schema from the registry.

        Note: AWS Glue doesn't support deletion via API, so this is a placeholder
        for future implementation. Currently just verifies the schema exists.

        Args:
            schema_name: Name of the schema to delete

        Raises:
            SchemaNotFoundError: If schema does not exist
        """
        schema = self.schema_registry.get_schema(schema_name)
        if not schema:
            raise SchemaNotFoundError(schema_name)
