"""Output ports (interfaces) for schema registry and table catalog operations."""

from abc import ABC, abstractmethod
from typing import Optional
from registry_api.domain.models import DataContract


class SchemaRegistryPort(ABC):
    """Output port for AWS Glue Schema Registry operations."""

    @abstractmethod
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
        pass

    @abstractmethod
    def get_schema(self, schema_name: str) -> Optional[dict]:
        """Get details of a schema by name.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details dict, or None if not found
        """
        pass

    @abstractmethod
    def list_schemas(self) -> list:
        """List all schemas in the registry.

        Returns:
            List of schema dicts
        """
        pass

    @abstractmethod
    def get_schema_versions(self, schema_name: str) -> Optional[dict]:
        """Get version information for a schema.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details including version information, or None if not found
        """
        pass

    @abstractmethod
    def list_all_schema_versions(self, schema_name: str) -> list:
        """Get all versions of a schema with their details.

        Args:
            schema_name: Name of the schema

        Returns:
            List of schema version details, or empty list if not found
        """
        pass
