"""Upload data contracts to AWS Glue Schema Registry."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import boto3


class SchemaRegistryClient:
    """Client for interacting with AWS Glue Schema Registry."""

    def __init__(
        self,
        registry_name: str = None,
        region: str = None,
    ):
        """Initialize the Schema Registry client.

        Args:
            registry_name: Name of the Glue Schema Registry (defaults to env var TF_VAR_registry_name)
            region: AWS region (defaults to AWS_DEFAULT_REGION env var or us-east-1)
        """
        self.registry_name = registry_name or os.getenv("TF_VAR_registry_name", "schema-registry")
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.glue = boto3.client("glue", region_name=self.region)

    def upload_schema_to_registry(
        self,
        contract,
        data_format: str = "AVRO",
        compatibility: str = "BACKWARD",
    ) -> str:
        """Upload a DataContract to AWS Glue Schema Registry.

        Args:
            contract: DataContract model instance
            data_format: Data format (AVRO, PROTOBUF, JSON)
            compatibility: Compatibility mode (NONE, DISABLED, BACKWARD, FORWARD, BOTH)

        Returns:
            Schema ARN
        """
        schema_name = contract.contract_id
        description = contract.description or f"Schema for {schema_name}"

        # Convert contract to AVRO schema
        schema_definition = self._contract_to_avro(contract)

        try:
            # Check if registry exists
            registry = self.glue.get_registry(RegistryId={"RegistryName": self.registry_name})
            registry_arn = registry["RegistryArn"]
        except self.glue.exceptions.EntityNotFoundException:
            raise ValueError(
                f"Registry '{self.registry_name}' not found. Create it first with Terraform."
            )

        # Build tags from metadata
        tags = {
            "ManagedBy": "python-api",
            "Source": "data-contract",
            "ContractVersion": contract.version,
        }
        if hasattr(contract, 'metadata') and contract.metadata:
            tags.update({
                "DataOwner": contract.metadata.data_owner,
                "DataOwnerEmail": contract.metadata.data_owner_email,
                "DataSteward": contract.metadata.data_steward,
                "DataStewardEmail": contract.metadata.data_steward_email,
                "SLAUptimePercentage": str(contract.metadata.sla_uptime_percentage),
                "SLAMaxLatencyMs": str(contract.metadata.sla_max_latency_ms),
            })

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

    def get_schema_detail(self, schema_name: str) -> dict:
        """Get details of a specific schema including tags/metadata.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema details dict with metadata
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
            return {}

    def get_schema_versions(self, schema_name: str) -> list:
        """Get all versions of a specific schema.

        Args:
            schema_name: Name of the schema

        Returns:
            List of schema versions
        """
        try:
            response = self.glue.get_schema_versions(
                SchemaId={
                    "RegistryName": self.registry_name,
                    "SchemaName": schema_name,
                }
            )
            return response.get("Schemas", [])
        except Exception:
            return []

    @staticmethod
    def _contract_to_avro(contract) -> str:
        """Convert a DataContract to AVRO schema format.

        Args:
            contract: DataContract model instance

        Returns:
            JSON string of AVRO schema
        """
        fields = []
        for col in contract.columns:
            field = {
                "name": col.name,
                "type": SchemaRegistryClient._map_type_to_avro(col.data_type),
            }
            if col.description:
                field["doc"] = col.description
            if col.nullable:
                field["type"] = ["null", field["type"]]
            fields.append(field)

        # Build comprehensive documentation including metadata
        doc = contract.description or ""
        if hasattr(contract, 'metadata') and contract.metadata:
            doc += f"\n\nMetadata:\n"
            doc += f"  Data Owner: {contract.metadata.data_owner} ({contract.metadata.data_owner_email})\n"
            doc += f"  Data Steward: {contract.metadata.data_steward} ({contract.metadata.data_steward_email})\n"
            doc += f"  SLA Uptime: {contract.metadata.sla_uptime_percentage}%\n"
            doc += f"  SLA Max Latency: {contract.metadata.sla_max_latency_ms}ms"

        schema = {
            "type": "record",
            "name": contract.name.replace(" ", ""),
            "namespace": "com.example.schema",
            "doc": doc,
            "fields": fields,
        }

        return json.dumps(schema)

    @staticmethod
    def _map_type_to_avro(data_type: str) -> str:
        """Map contract data types to AVRO types.

        Args:
            data_type: Contract data type

        Returns:
            AVRO type
        """
        type_map = {
            "string": "string",
            "integer": "int",
            "number": "double",
            "boolean": "boolean",
            "date": "string",
            "timestamp": "string",
            "object": "string",
            "array": "array",
        }
        return type_map.get(data_type, "string")


def upload_schema_to_registry(
    registry_name: str,
    schema_name: str,
    schema_file: Path,
    data_format: str = "AVRO",
    compatibility: str = "BACKWARD",
    description: str = "",
    region: str = "us-east-1",
) -> dict:
    """Upload a schema to AWS Glue Schema Registry.

    Args:
        registry_name: Name of the Glue Schema Registry
        schema_name: Name for the schema
        schema_file: Path to the contract JSON file
        data_format: Data format (AVRO, PROTOBUF, JSON)
        compatibility: Compatibility mode (NONE, DISABLED, BACKWARD, FORWARD, BOTH)
        description: Schema description
        region: AWS region

    Returns:
        Response from Glue API
    """
    # Read the contract file
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file, "r") as f:
        contract = json.load(f)

    # Extract or create schema definition
    # If it's a data contract (has columns), convert to AVRO schema
    if "columns" in contract:
        schema_definition = _convert_contract_to_avro(contract)
    else:
        # Assume it's already a proper schema definition
        schema_definition = json.dumps(contract)

    # Create Glue client
    glue = boto3.client("glue", region_name=region)

    try:
        # Check if registry exists
        registry = glue.get_registry(RegistryId={"RegistryName": registry_name})
        registry_arn = registry["RegistryArn"]
        print(f"✅ Found registry: {registry_name} (ARN: {registry_arn})")
    except glue.exceptions.EntityNotFoundException:
        raise ValueError(f"Registry '{registry_name}' not found. Create it first with Terraform.")

    try:
        # Try to get existing schema
        existing = glue.get_schema(
            SchemaId={"RegistryName": registry_name, "SchemaName": schema_name}
        )
        version = existing["LatestSchemaVersion"]
        print(f"✅ Found existing schema: {schema_name} (v{version})")
        updating = True
    except glue.exceptions.EntityNotFoundException:
        print(f"📝 Creating new schema: {schema_name}")
        updating = False

    if updating:
        # Add new version to existing schema
        response = glue.put_schema_version(
            RegistryId={"RegistryName": registry_name},
            SchemaName=schema_name,
            DataFormat=data_format,
            Compatibility=compatibility,
            SchemaDefinition=schema_definition,
        )
        print(f"✅ Schema version updated: v{response['VersionNumber']}")
    else:
        # Create new schema
        response = glue.create_schema(
            RegistryId={"RegistryName": registry_name},
            SchemaName=schema_name,
            DataFormat=data_format,
            Compatibility=compatibility,
            Description=description or f"Schema for {schema_name}",
            SchemaDefinition=schema_definition,
            Tags={"ManagedBy": "python", "Source": "data-contract"},
        )
        print(f"✅ Schema created: {schema_name}")
        print(f"   ARN: {response['SchemaArn']}")
        print(f"   Version: {response['VersionNumber']}")

    return response


def _convert_contract_to_avro(contract: dict) -> str:
    """Convert a data contract to AVRO schema format.

    Args:
        contract: Data contract dict with 'columns' field

    Returns:
        JSON string of AVRO schema
    """
    columns = contract.get("columns", [])
    name = contract.get("name", "Record").replace(" ", "")

    fields = []
    for col in columns:
        field = {
            "name": col["name"],
            "type": _map_type_to_avro(col["data_type"]),
        }
        if col.get("description"):
            field["doc"] = col["description"]
        if col.get("nullable"):
            field["type"] = ["null", field["type"]]
        fields.append(field)

    schema = {
        "type": "record",
        "name": name,
        "namespace": "com.example.schema",
        "doc": contract.get("description", ""),
        "fields": fields,
    }

    return json.dumps(schema)


def _map_type_to_avro(data_type: str) -> str:
    """Map contract data types to AVRO types.

    Args:
        data_type: Contract data type (string, integer, date, etc.)

    Returns:
        AVRO type
    """
    type_map = {
        "string": "string",
        "integer": "int",
        "number": "double",
        "boolean": "boolean",
        "date": "string",  # AVRO doesn't have date, use string with format
        "timestamp": "string",
        "object": "string",
        "array": "array",
    }
    return type_map.get(data_type, "string")


def list_schemas(registry_name: str, region: str = "us-east-1") -> None:
    """List all schemas in a registry.

    Args:
        registry_name: Name of the Glue Schema Registry
        region: AWS region
    """
    glue = boto3.client("glue", region_name=region)

    try:
        schemas = glue.list_schemas(RegistryId={"RegistryName": registry_name})
        print(f"\n📋 Schemas in '{registry_name}':")
        for schema in schemas.get("Schemas", []):
            print(f"  - {schema['SchemaName']} (v{schema['LatestSchemaVersion']})")
    except glue.exceptions.EntityNotFoundException:
        print(f"❌ Registry '{registry_name}' not found")


def main():
    """CLI for uploading schemas."""
    import argparse

    parser = argparse.ArgumentParser(description="Upload schemas to AWS Glue Schema Registry")
    parser.add_argument(
        "command",
        choices=["upload", "list"],
        help="Command to execute",
    )
    parser.add_argument(
        "--registry",
        default="schema-registry",
        help="Registry name (default: schema-registry)",
    )
    parser.add_argument(
        "--schema-name",
        help="Schema name (required for upload)",
    )
    parser.add_argument(
        "--contract-file",
        type=Path,
        help="Path to contract JSON file (required for upload)",
    )
    parser.add_argument(
        "--format",
        default="AVRO",
        choices=["AVRO", "PROTOBUF", "JSON"],
        help="Data format (default: AVRO)",
    )
    parser.add_argument(
        "--compatibility",
        default="BACKWARD",
        choices=["NONE", "DISABLED", "BACKWARD", "FORWARD", "BOTH"],
        help="Compatibility mode (default: BACKWARD)",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    args = parser.parse_args()

    try:
        if args.command == "upload":
            if not args.schema_name or not args.contract_file:
                parser.error("--schema-name and --contract-file required for upload command")

            upload_schema_to_registry(
                registry_name=args.registry,
                schema_name=args.schema_name,
                schema_file=args.contract_file,
                data_format=args.format,
                compatibility=args.compatibility,
                region=args.region,
            )
        elif args.command == "list":
            list_schemas(registry_name=args.registry, region=args.region)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()