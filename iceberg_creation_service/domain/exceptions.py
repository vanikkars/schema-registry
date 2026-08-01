"""Domain exceptions."""


class IcebergTableError(Exception):
    """Base exception for Iceberg table operations."""
    pass


class TableCreationError(IcebergTableError):
    """Raised when table creation fails."""
    pass


class TableNotFoundError(IcebergTableError):
    """Raised when a table is not found."""
    pass


class InvalidTableError(IcebergTableError):
    """Raised when table data is invalid."""
    pass


class SchemaEvolutionError(IcebergTableError):
    """Raised when schema evolution rules are violated."""
    pass