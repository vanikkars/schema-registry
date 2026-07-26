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
    """Register a new schema in AWS Glue Schema Registry."""
    try:
        schema_arn = schema_registry_client.upload_schema_to_registry(contract)
        # Get schema details
        schema_details = schema_registry_client.get_schema_detail(contract.contract_id)

        return {
            "status": "success",
            "message": "Schema registered successfully",
            "schema_arn": schema_arn,
            "schema_name": contract.contract_id,
            "version": contract.version,
            "metadata": contract.metadata.dict() if contract.metadata else {},
            "schema_details": {
                "Description": schema_details.get("Description", ""),
                "CreatedTime": str(schema_details.get("CreatedTime", "")),
                "UpdatedTime": str(schema_details.get("UpdatedTime", "")),
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