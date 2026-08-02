"""Domain models - Iceberg table entities and value objects."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from iceberg_creation_service.domain.exceptions import InvalidTableError


class DataType(Enum):
    """AVRO data types."""
    STRING = "string"
    INT = "int"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    BYTES = "bytes"
    DATE = "date"
    TIMESTAMP = "timestamp"

    def to_glue_type(self) -> str:
        """Map to AWS Glue type."""
        mapping = {
            DataType.STRING: "string",
            DataType.INT: "int",
            DataType.LONG: "bigint",
            DataType.FLOAT: "float",
            DataType.DOUBLE: "double",
            DataType.BOOLEAN: "boolean",
            DataType.BYTES: "binary",
            DataType.DATE: "date",
            DataType.TIMESTAMP: "timestamp",
        }
        return mapping[self]


@dataclass(frozen=True)
class Column:
    """Immutable column definition."""
    name: str
    data_type: DataType
    description: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Column name cannot be empty")

    def to_glue_format(self) -> dict:
        """Convert to AWS Glue column format."""
        return {
            "Name": self.name,
            "Type": self.data_type.to_glue_type(),
            "Comment": self.description or "",
        }


@dataclass
class IcebergTable:
    """Iceberg table domain model."""
    table_name: str
    contract_id: str
    version: str
    columns: List[Column]
    database_name: str = "iceberg_tables"
    description: Optional[str] = None
    data_owner: Optional[str] = None
    data_steward: Optional[str] = None
    s3_location: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        """Validate table business rules."""
        if not self.table_name:
            raise InvalidTableError("Table name cannot be empty")
        if not self.columns:
            raise InvalidTableError("Table must have at least one column")
        if len(self.columns) > 1000:
            raise InvalidTableError("Table cannot have more than 1000 columns")

        # Check for duplicate column names
        column_names = {col.name for col in self.columns}
        if len(column_names) != len(self.columns):
            raise InvalidTableError("Duplicate column names detected")

    def to_glue_columns(self) -> List[dict]:
        """Convert columns to Glue format."""
        return [col.to_glue_format() for col in self.columns]

    def get_table_parameters(self) -> dict:
        """Get AWS Glue table parameters."""
        return {
            "EXTERNAL": "TRUE",
            "table_type": "ICEBERG",
            "contract_id": self.contract_id,
            "iceberg_table_version": str(self.version),
            "created_at": self.created_at.isoformat(),
            "data_owner": self.data_owner or "Unknown",
            "data_steward": self.data_steward or "Unknown",
        }


@dataclass
class SchemaChange:
    """Represents a schema change during evolution."""
    added_columns: List[Column] = field(default_factory=list)
    removed_columns: List[Column] = field(default_factory=list)
    modified_columns: List[tuple] = field(default_factory=list)  # (old, new) pairs

    def get_changes(self) -> List[str]:
        """Get list of changes."""
        changes = []
        for col in self.added_columns:
            changes.append(f"Added column: {col.name} ({col.data_type.value})")
        for old, new in self.modified_columns:
            if old.data_type != new.data_type:
                changes.append(
                    f"Modified column type: {old.name} ({old.data_type.value} → {new.data_type.value})"
                )
        return changes

    def get_warnings(self) -> List[str]:
        """Get warnings about potentially risky changes."""
        warnings = []
        if self.removed_columns:
            for col in self.removed_columns:
                warnings.append(f"Removed column: {col.name} (data will be lost)")
        for old, new in self.modified_columns:
            if old.data_type != new.data_type:
                warnings.append(
                    f"Modified column type: {old.name} ({old.data_type.value} → {new.data_type.value})"
                )
        return warnings