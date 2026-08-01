"""Value Objects - Immutable objects with no identity."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class DataType(Enum):
    """AVRO data types supported by the system."""
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
        """Map AVRO type to AWS Glue type."""
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
class TableName:
    """Immutable table name value object."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Table name must be a non-empty string")
        if len(self.value) > 255:
            raise ValueError("Table name must not exceed 255 characters")

    def normalize(self) -> "TableName":
        """Normalize table name (lowercase, replace hyphens with underscores)."""
        normalized = self.value.replace("-", "_").lower()
        return TableName(normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ContractId:
    """Immutable contract ID value object."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Contract ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Version:
    """Immutable version value object."""
    major: int
    minor: int = 0
    patch: int = 0

    def __post_init__(self):
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers must be non-negative")

    @classmethod
    def from_int(cls, version: int) -> "Version":
        """Create version from single integer (e.g., 1 -> 1.0.0)."""
        if version < 0:
            raise ValueError("Version must be non-negative")
        return cls(major=version)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class Column:
    """Immutable column definition value object."""
    name: str
    data_type: DataType
    description: Optional[str] = None

    def __post_init__(self):
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Column name must be a non-empty string")
        if len(self.name) > 128:
            raise ValueError("Column name must not exceed 128 characters")

    def to_glue_format(self) -> dict:
        """Convert to AWS Glue column format."""
        return {
            "Name": self.name,
            "Type": self.data_type.to_glue_type(),
            "Comment": self.description or "",
        }


@dataclass(frozen=True)
class DatabaseName:
    """Immutable database name value object."""
    value: str = "iceberg_tables"

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Database name must be a non-empty string")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class S3Location:
    """Immutable S3 location value object."""
    value: str

    def __post_init__(self):
        if not self.value.startswith("s3://"):
            raise ValueError("S3 location must start with 's3://'")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TableMetadata:
    """Immutable table metadata value object."""
    data_owner: Optional[str] = None
    data_steward: Optional[str] = None

    def to_glue_parameters(self) -> dict:
        """Convert to AWS Glue table parameters."""
        return {
            "data_owner": self.data_owner or "Unknown",
            "data_steward": self.data_steward or "Unknown",
        }


@dataclass(frozen=True)
class TableStatus:
    """Immutable table status value object."""
    value: str

    # Status constants
    CREATED = "created"
    EXISTS = "exists"
    UPDATED = "updated"
    FAILED = "failed"

    def __post_init__(self):
        valid_statuses = {self.CREATED, self.EXISTS, self.UPDATED, self.FAILED}
        if self.value not in valid_statuses:
            raise ValueError(f"Invalid status: {self.value}")

    def is_success(self) -> bool:
        """Check if status represents a successful operation."""
        return self.value in {self.CREATED, self.EXISTS, self.UPDATED}

    def __str__(self) -> str:
        return self.value