"""Schema Registry API endpoints - REST compliant."""

from fastapi import APIRouter, HTTPException, Query, Response, status
from typing import Optional
from .models import DataContract
from .upload_to_glue import SchemaRegistryClient

router = APIRouter(prefix="/api/v1/schemas", tags=["schemas"])

schema_registry_client = SchemaRegistryClient()


@router.post("", status_code=status.HTTP_201_CREATED, tags=["schemas"])
async def create_schema(contract: DataContract, response: Response) -> dict:
    """Create a new schema in AWS Glue Schema Registry and Iceberg table.

    Returns 201 Created with Location header pointing to created resource.
    """
    try:
        # 1. Register schema in Glue Schema Registry
        schema_arn = schema_registry_client.upload_schema_to_registry(contract)
        schema_details = schema_registry_client.get_schema_detail(contract.contract_id)

        # 2. Create Iceberg table from schema
        table_info = schema_registry_client.create_iceberg_table(contract)

        # Set Location header to created resource
        response.headers["Location"] = f"/api/v1/schemas/{contract.contract_id}"

        return {
            "data": {
                "schema": {
                    "arn": schema_arn,
                    "name": contract.contract_id,
                    "version": contract.version,
                    "description": schema_details.get("Description", ""),
                    "latest_version": schema_details.get("LatestSchemaVersion", 0),
                    "next_version": schema_details.get("NextSchemaVersion", 0),
                    "checkpoint": schema_details.get("SchemaCheckpoint", ""),
                    "status": schema_details.get("SchemaStatus", "AVAILABLE"),
                    "data_format": schema_details.get("DataFormat", "AVRO"),
                    "compatibility": schema_details.get("Compatibility", "BACKWARD"),
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.data_type,
                            "nullable": col.nullable,
                            "description": col.description,
                        }
                        for col in contract.columns
                    ],
                    "metadata": contract.metadata.model_dump() if contract.metadata else {},
                    "created_at": str(schema_details.get("CreatedTime", "")),
                    "updated_at": str(schema_details.get("UpdatedTime", "")),
                },
                "table": {
                    "name": table_info["table_name"],
                    "database": table_info["database_name"],
                    "location": table_info["s3_location"],
                    "status": table_info["status"],
                }
            }
        }
    except ValueError as e:
        # Schema registry not found, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schema"
        )


@router.get("", tags=["schemas"])
async def list_schemas(
    limit: Optional[int] = Query(20, ge=1, le=100),
    offset: Optional[int] = Query(0, ge=0),
) -> dict:
    """List all schemas in the registry with pagination support."""
    try:
        schemas = schema_registry_client.list_schemas()

        # Paginate results
        total = len(schemas)
        paginated = schemas[offset : offset + limit]

        return {
            "data": paginated,
            "meta": {
                "total": total,
                "count": len(paginated),
                "limit": limit,
                "offset": offset,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schemas"
        )


@router.get("/{schema_name}", tags=["schemas"])
async def get_schema(schema_name: str) -> dict:
    """Get details of a specific schema by name."""
    try:
        schema = schema_registry_client.get_schema_detail(schema_name)

        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema '{schema_name}' not found"
            )

        # Format response with key fields
        return {
            "data": {
                "name": schema.get("SchemaName"),
                "arn": schema.get("SchemaArn"),
                "description": schema.get("Description", ""),
                "status": schema.get("SchemaStatus", "AVAILABLE"),
                "data_format": schema.get("DataFormat", "AVRO"),
                "compatibility": schema.get("Compatibility", "BACKWARD"),
                "latest_version": schema.get("LatestSchemaVersion", 0),
                "next_version": schema.get("NextSchemaVersion", 0),
                "checkpoint": schema.get("SchemaCheckpoint", ""),
                "created_time": schema.get("CreatedTime"),
                "updated_time": schema.get("UpdatedTime"),
                "registry_name": schema.get("RegistryName"),
                "registry_arn": schema.get("RegistryArn"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schema"
        )


@router.get("/{schema_name}/versions", tags=["schemas"])
async def get_schema_versions(schema_name: str) -> dict:
    """Get version information for a specific schema."""
    try:
        version_info = schema_registry_client.get_schema_versions(schema_name)

        if not version_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema '{schema_name}' not found"
            )

        return {
            "data": version_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schema versions"
        )


@router.get("/{schema_name}/versions/{version}", tags=["schemas"])
async def get_schema_version(schema_name: str, version: str) -> dict:
    """Get a specific version of a schema.

    Note: AWS Glue Schema Registry tracks only the latest version.
    This endpoint returns the current schema if version matches latest.
    """
    try:
        version_info = schema_registry_client.get_schema_versions(schema_name)

        if not version_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema '{schema_name}' not found"
            )

        # Check if requested version matches latest
        latest_version = version_info.get("latest_version", 0)
        try:
            requested_version = int(version)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid version format: '{version}'"
            )

        if requested_version != latest_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version '{version}' not found (latest: {latest_version})"
            )

        return {
            "data": version_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schema version"
        )


@router.delete("/{schema_name}", status_code=status.HTTP_204_NO_CONTENT, tags=["schemas"])
async def delete_schema(schema_name: str) -> None:
    """Delete a schema from the registry.

    Note: AWS Glue Schema Registry doesn't support deletion via API.
    This endpoint is a placeholder for future implementation.
    """
    try:
        # Verify schema exists
        schema = schema_registry_client.get_schema_detail(schema_name)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema '{schema_name}' not found"
            )

        # AWS Glue doesn't support schema deletion, so we just return 204 No Content
        # In a future version, this could deactivate or archive the schema
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schema"
        )