"""FastAPI service for schema registry management."""

from typing import Optional

import boto3
from fastapi import APIRouter, HTTPException, status

from contracts_management.models import DataContract
from contracts_management.upload_to_glue import (
    _convert_contract_to_avro,
    _map_type_to_avro,
)

router = APIRouter(prefix="/api/v1/schemas", tags=["schemas"])


class SchemaRegistryClient:
    """Client for interacting with AWS Glue Schema Registry."""

    def __init__(self, region: str = "us-east-1"):
        self.glue = boto3.client("glue", region_name=region)
        self.region = region

    def register_schema(
        self,
        registry_name: str,
        contract: DataContract,
        schema_name: Optional[str] = None,
    ) -> dict:
        """Register a schema from a data contract.

        Args:
            registry_name: Name of the Glue Schema Registry
            contract: DataContract object
            schema_name: Optional override for schema name

        Returns:
            Response from Glue API
        """
        schema_name = schema_name or contract.contract_id

        # Check if registry exists
        try:
            registry = self.glue.get_registry(RegistryId={"RegistryName": registry_name})
        except self.glue.exceptions.EntityNotFoundException:
            raise ValueError(f"Registry '{registry_name}' not found")

        # Convert contract to AVRO schema
        schema_definition = _convert_contract_to_avro(contract.model_dump())

        try:
            # Try to get existing schema
            existing = self.glue.get_schema(
                SchemaId={"RegistryName": registry_name, "SchemaName": schema_name}
            )
            # Add new version
            response = self.glue.put_schema_version(
                RegistryId={"RegistryName": registry_name},
                SchemaName=schema_name,
                DataFormat="AVRO",
                Compatibility="BACKWARD",
                SchemaDefinition=schema_definition,
            )
            response["action"] = "updated"
            response["version"] = response["VersionNumber"]
        except self.glue.exceptions.EntityNotFoundException:
            # Create new schema
            response = self.glue.create_schema(
                RegistryId={"RegistryName": registry_name},
                SchemaName=schema_name,
                DataFormat="AVRO",
                Compatibility="BACKWARD",
                Description=contract.description,
                SchemaDefinition=schema_definition,
                Tags={
                    "ManagedBy": "fastapi",
                    "ContractId": contract.contract_id,
                    "Version": contract.version,
                },
            )
            response["action"] = "created"
            response["version"] = response["VersionNumber"]

        return response

    def list_schemas(self, registry_name: str) -> dict:
        """List all schemas in a registry.

        Args:
            registry_name: Name of the Glue Schema Registry

        Returns:
            List of schemas
        """
        try:
            response = self.glue.list_schemas(RegistryId={"RegistryName": registry_name})
            return response
        except self.glue.exceptions.EntityNotFoundException:
            raise ValueError(f"Registry '{registry_name}' not found")

    def get_schema(self, registry_name: str, schema_name: str) -> dict:
        """Get schema details.

        Args:
            registry_name: Name of the Glue Schema Registry
            schema_name: Name of the schema

        Returns:
            Schema details
        """
        try:
            response = self.glue.get_schema(
                SchemaId={"RegistryName": registry_name, "SchemaName": schema_name}
            )
            return response
        except self.glue.exceptions.EntityNotFoundException:
            raise ValueError(f"Schema '{schema_name}' not found in registry '{registry_name}'")


# Initialize client
registry_client = SchemaRegistryClient()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_schema(
    contract: DataContract,
    registry_name: str = "schema-registry",
    schema_name: Optional[str] = None,
) -> dict:
    """Register a data contract to AWS Glue Schema Registry.

    Args:
        contract: DataContract object
        registry_name: Name of the registry (default: schema-registry)
        schema_name: Optional custom schema name

    Returns:
        Schema registration response

    Raises:
        HTTPException: If registry not found or registration fails
    """
    try:
        response = registry_client.register_schema(
            registry_name=registry_name,
            contract=contract,
            schema_name=schema_name,
        )
        return {
            "success": True,
            "action": response.get("action", "unknown"),
            "schema_name": response.get("SchemaName", schema_name or contract.contract_id),
            "schema_arn": response.get("SchemaArn"),
            "version": response.get("version"),
            "registry_name": registry_name,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register schema: {str(e)}",
        )


@router.get("/list")
async def list_schemas(registry_name: str = "schema-registry") -> dict:
    """List all schemas in a registry.

    Args:
        registry_name: Name of the registry (default: schema-registry)

    Returns:
        List of schemas

    Raises:
        HTTPException: If registry not found
    """
    try:
        response = registry_client.list_schemas(registry_name=registry_name)
        schemas = [
            {
                "name": schema["SchemaName"],
                "latest_version": schema["LatestSchemaVersion"],
                "arn": schema.get("SchemaArn"),
                "created_time": str(schema.get("CreatedTime")),
                "updated_time": str(schema.get("UpdatedTime")),
            }
            for schema in response.get("Schemas", [])
        ]
        return {
            "success": True,
            "registry_name": registry_name,
            "schema_count": len(schemas),
            "schemas": schemas,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list schemas: {str(e)}",
        )


@router.get("/detail/{schema_name}")
async def get_schema(
    schema_name: str,
    registry_name: str = "schema-registry",
) -> dict:
    """Get details of a specific schema.

    Args:
        schema_name: Name of the schema
        registry_name: Name of the registry (default: schema-registry)

    Returns:
        Schema details

    Raises:
        HTTPException: If schema or registry not found
    """
    try:
        response = registry_client.get_schema(
            registry_name=registry_name,
            schema_name=schema_name,
        )
        return {
            "success": True,
            "schema_name": response.get("SchemaName"),
            "schema_arn": response.get("SchemaArn"),
            "data_format": response.get("DataFormat"),
            "compatibility": response.get("Compatibility"),
            "description": response.get("Description"),
            "latest_version": response.get("LatestSchemaVersion"),
            "created_time": str(response.get("CreatedTime")),
            "updated_time": str(response.get("UpdatedTime")),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema: {str(e)}",
        )