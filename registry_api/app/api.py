"""Schema Registry API endpoints."""

import json
import boto3
from fastapi import APIRouter, HTTPException
from contracts_management.models import DataContract
from contracts_management.upload_to_glue import SchemaRegistryClient

router = APIRouter(prefix="/api/v1/schemas", tags=["schemas"])

schema_registry_client = SchemaRegistryClient()


@router.post("/register", tags=["schemas"])
async def register_schema(contract: DataContract) -> dict:
    """Register a new schema in AWS Glue Schema Registry and create Iceberg table."""
    try:
        # 1. Register schema in Glue Schema Registry
        schema_arn = schema_registry_client.upload_schema_to_registry(contract)
        schema_details = schema_registry_client.get_schema_detail(contract.contract_id)

        # 2. Create Iceberg table from schema
        table_info = schema_registry_client.create_iceberg_table(contract)

        return {
            "status": "success",
            "message": "Schema registered and Iceberg table created successfully",
            "schema": {
                "schema_arn": schema_arn,
                "schema_name": contract.contract_id,
                "version": contract.version,
                "description": schema_details.get("Description", ""),
                "metadata": contract.metadata.model_dump() if contract.metadata else {},
                "created_at": str(schema_details.get("CreatedTime", "")),
                "updated_at": str(schema_details.get("UpdatedTime", "")),
            },
            "table": {
                "table_name": table_info["table_name"],
                "database_name": table_info["database_name"],
                "s3_location": table_info["s3_location"],
                "status": table_info["status"],
                "message": table_info["message"],
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register schema: {str(e)}")


@router.get("/list", tags=["schemas"])
async def list_schemas() -> dict:
    """List all schemas in the registry."""
    try:
        schemas = schema_registry_client.list_schemas()
        return {
            "status": "success",
            "count": len(schemas),
            "schemas": schemas,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schemas: {str(e)}")


@router.get("/detail/{schema_name}", tags=["schemas"])
async def get_schema_detail(schema_name: str) -> dict:
    """Get details of a specific schema including metadata."""
    try:
        schema = schema_registry_client.get_schema_detail(schema_name)
        return {
            "status": "success",
            "schema": schema,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema detail: {str(e)}")


@router.get("/versions/{schema_name}", tags=["schemas"])
async def get_schema_versions(schema_name: str) -> dict:
    """Get all versions of a schema."""
    try:
        versions = schema_registry_client.get_schema_versions(schema_name)
        return {
            "status": "success",
            "schema_name": schema_name,
            "count": len(versions),
            "versions": versions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema versions: {str(e)}")