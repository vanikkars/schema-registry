"""Domain Entities - Objects with identity and lifecycle."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from iceberg_creation_service.domain.value_objects import (
    TableName,
    ContractId,
    Version,
    Column,
    DatabaseName,
    S3Location,
    TableMetadata,
    TableStatus,
)


@dataclass
class IcebergTable:
    """
    Iceberg Table aggregate root.

    Represents an Iceberg table with all its properties and business logic.
    This is the primary domain entity that encapsulates table management.
    """
    table_name: TableName
    contract_id: ContractId
    version: Version
    columns: List[Column] = field(default_factory=list)
    database_name: DatabaseName = field(default_factory=DatabaseName)
    s3_location: Optional[S3Location] = None
    metadata: TableMetadata = field(default_factory=TableMetadata)
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: TableStatus = field(default_factory=lambda: TableStatus(TableStatus.CREATED))

    def validate(self) -> None:
        """Validate table business rules."""
        if not self.columns:
            raise ValueError("Table must have at least one column")

        if len(self.columns) > 1000:
            raise ValueError("Table cannot have more than 1000 columns")

        # Check for duplicate column names
        column_names = {col.name for col in self.columns}
        if len(column_names) != len(self.columns):
            raise ValueError("Duplicate column names detected")

    def update_schema(self, new_columns: List[Column]) -> "SchemaEvolution":
        """
        Detect schema changes when updating table.

        Returns SchemaEvolution with detailed change information.
        """
        self.validate_schema_update(new_columns)

        old_col_names = {col.name: col for col in self.columns}
        new_col_names = {col.name: col for col in new_columns}

        added = [col for col in new_columns if col.name not in old_col_names]
        removed = [col for col in self.columns if col.name not in new_col_names]
        modified = [
            (old_col_names[col.name], col)
            for col in new_columns
            if col.name in old_col_names and old_col_names[col.name].data_type != col.data_type
        ]

        evolution = SchemaEvolution(
            added_columns=added,
            removed_columns=removed,
            modified_columns=modified,
            table_name=self.table_name,
        )

        # Apply changes
        self.columns = new_columns
        self.updated_at = datetime.utcnow()

        return evolution

    def validate_schema_update(self, new_columns: List[Column]) -> None:
        """Validate schema evolution rules."""
        if not new_columns:
            raise ValueError("Cannot remove all columns")

        # Check for duplicate column names in new schema
        column_names = {col.name for col in new_columns}
        if len(column_names) != len(new_columns):
            raise ValueError("Duplicate column names detected in updated schema")

    def mark_as_created(self) -> None:
        """Mark table as successfully created."""
        self.status = TableStatus(TableStatus.CREATED)
        self.updated_at = datetime.utcnow()

    def mark_as_exists(self) -> None:
        """Mark table as already existing."""
        self.status = TableStatus(TableStatus.EXISTS)
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self) -> None:
        """Mark table as failed to create."""
        self.status = TableStatus(TableStatus.FAILED)
        self.updated_at = datetime.utcnow()


@dataclass
class SchemaEvolution:
    """
    Value object representing schema changes.

    Captures all changes during a schema update for audit and reporting.
    """
    table_name: TableName
    added_columns: List[Column] = field(default_factory=list)
    removed_columns: List[Column] = field(default_factory=list)
    modified_columns: List[tuple] = field(default_factory=list)  # List of (old, new) tuples

    def has_changes(self) -> bool:
        """Check if there are any schema changes."""
        return bool(self.added_columns or self.removed_columns or self.modified_columns)

    def get_change_summary(self) -> dict:
        """Get a summary of changes for reporting."""
        return {
            "table_name": str(self.table_name),
            "added_columns": [col.name for col in self.added_columns],
            "removed_columns": [col.name for col in self.removed_columns],
            "modified_columns": [
                {"name": old.name, "from": old.data_type.value, "to": new.data_type.value}
                for old, new in self.modified_columns
            ],
        }

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

    def get_changes(self) -> List[str]:
        """Get detailed list of changes."""
        changes = []

        for col in self.added_columns:
            changes.append(f"Added column: {col.name} ({col.data_type.value})")

        for old, new in self.modified_columns:
            if old.data_type != new.data_type:
                changes.append(
                    f"Modified column type: {old.name} ({old.data_type.value} → {new.data_type.value})"
                )

        return changes