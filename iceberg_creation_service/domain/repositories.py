"""Repository interfaces - Data access abstraction."""

from abc import ABC, abstractmethod
from typing import Optional

from iceberg_creation_service.domain.entities import IcebergTable
from iceberg_creation_service.domain.value_objects import TableName


class IcebergTableRepository(ABC):
    """
    Repository interface for Iceberg table persistence.

    Abstracts away the details of how tables are stored (AWS Glue, database, etc).
    """

    @abstractmethod
    async def save(self, table: IcebergTable) -> None:
        """
        Persist a table to storage.

        Args:
            table: The IcebergTable to persist

        Raises:
            TableCreationError: If save operation fails
        """
        pass

    @abstractmethod
    async def get_by_name(self, table_name: TableName) -> Optional[IcebergTable]:
        """
        Retrieve a table by name.

        Args:
            table_name: The table name to look up

        Returns:
            The IcebergTable if found, None otherwise

        Raises:
            TableNotFoundError: If table lookup fails
        """
        pass

    @abstractmethod
    async def exists(self, table_name: TableName) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: The table name to check

        Returns:
            True if table exists, False otherwise
        """
        pass

    @abstractmethod
    async def update(self, table: IcebergTable) -> None:
        """
        Update an existing table's schema.

        Args:
            table: The IcebergTable with updated schema

        Raises:
            TableNotFoundError: If table does not exist
            TableCreationError: If update operation fails
        """
        pass

    @abstractmethod
    async def create_database_if_not_exists(self, database_name: str) -> None:
        """
        Ensure the database exists.

        Args:
            database_name: The database to create if needed

        Raises:
            TableCreationError: If database creation fails
        """
        pass