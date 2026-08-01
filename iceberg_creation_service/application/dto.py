"""Data Transfer Objects - Application layer contracts."""

from pydantic import BaseModel, Field
from typing import Optional, List
from dataclasses import dataclass


# Input DTOs

class CreateTableColumnDto(BaseModel):
    """Column definition input DTO."""
    name: str
    data_type: str
    description: Optional[str] = None


class CreateTableInputDto(BaseModel):
    """Create table input DTO."""
    contract_id: str = Field(..., description="Unique contract identifier")
    name: str = Field(..., description="Human-readable contract name")
    version: int = Field(default=1, description="Contract version")
    description: Optional[str] = None
    columns: List[CreateTableColumnDto] = Field(..., description="Table columns")
    data_owner: Optional[str] = None
    data_steward: Optional[str] = None
    database_name: Optional[str] = None
    s3_location: Optional[str] = None


class UpdateTableSchemaInputDto(BaseModel):
    """Update table schema input DTO."""
    contract_id: str
    name: str
    version: int
    columns: List[CreateTableColumnDto]
    description: Optional[str] = None
    database_name: Optional[str] = None


# Output DTOs

@dataclass
class CreateTableOutputDto:
    """Create table output DTO."""
    status: str
    table_name: str
    database_name: str
    s3_location: Optional[str] = None
    message: str = ""
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "status": self.status,
            "table_name": self.table_name,
            "database_name": self.database_name,
            "s3_location": self.s3_location,
            "message": self.message,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class UpdateTableSchemaOutputDto:
    """Update table schema output DTO."""
    status: str
    table_name: str
    database_name: str
    message: str = ""
    changes: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.changes is None:
            self.changes = []
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "status": self.status,
            "table_name": self.table_name,
            "database_name": self.database_name,
            "message": self.message,
            "changes": self.changes,
            "warnings": self.warnings,
        }


@dataclass
class GetTableInfoOutputDto:
    """Get table info output DTO."""
    table_name: str
    database_name: str
    columns: List[dict]
    location: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "table_name": self.table_name,
            "database_name": self.database_name,
            "columns": self.columns,
            "location": self.location,
        }