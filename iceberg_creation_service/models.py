"""Data models for Iceberg Creation Service."""

from pydantic import BaseModel, Field
from typing import Optional, List


class Column(BaseModel):
    """Table column definition."""

    name: str
    data_type: str
    description: Optional[str] = None


class Metadata(BaseModel):
    """Contract metadata."""

    data_owner: Optional[str] = None
    data_steward: Optional[str] = None


class CreateTableRequest(BaseModel):
    """Request to create an Iceberg table."""

    contract_id: str = Field(..., description="Unique contract identifier")
    name: str = Field(..., description="Human-readable contract name")
    version: int = Field(default=1, description="Contract version")
    description: Optional[str] = None
    columns: List[Column] = Field(..., description="Table columns")
    metadata: Optional[Metadata] = None
    database_name: Optional[str] = Field(
        default=None, description="Glue database (defaults to iceberg_tables)"
    )
    s3_location: Optional[str] = Field(
        default=None, description="S3 location for table (auto-generated if None)"
    )


class TableCreationResponse(BaseModel):
    """Response from table creation."""

    status: str
    table_name: str
    database_name: str
    s3_location: Optional[str] = None
    message: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)