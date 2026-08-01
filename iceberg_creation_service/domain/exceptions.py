"""Domain Exceptions - Business logic errors."""


class DomainException(Exception):
    """Base exception for all domain-level errors."""
    pass


class TableCreationError(DomainException):
    """Raised when table creation fails."""
    pass


class TableNotFoundError(DomainException):
    """Raised when a table is not found."""
    pass


class InvalidTableError(DomainException):
    """Raised when table data is invalid."""
    pass


class SchemaEvolutionError(DomainException):
    """Raised when schema evolution rules are violated."""
    pass


class InvalidDataTypeError(DomainException):
    """Raised when an unsupported data type is used."""
    pass


class DuplicateTableError(DomainException):
    """Raised when attempting to create a table that already exists."""
    pass