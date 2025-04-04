"""
Contains the base error classes.
"""

# Standard Library Imports
from uuid import UUID

# Third Party Imports

# Local Imports

# Constants
__all__ = [
    "DatabaseException"
]


class DatabaseException(Exception):
    """
    Base exception for database errors.
    """
    table: str
    identifier: str | int | UUID

    def __init__(
            self,
            table: str,
            identifier: str | int | UUID
    ) -> None:
        """
        Initialise the exception.
        """
        self.table = table
        self.identifier = identifier
        super().__init__(
            f"Error in {table} with key {identifier}."
        )


class DoesNotExist(DatabaseException):
    """
    Exception for when an object does not exist.
    """
    obj_name: str

    def __init__(
            self,
            obj_name: str,
            table: str,
            identifier: str | int | UUID
    ) -> None:
        """
        Initialise the exception.
        """
        super().__init__(table, identifier)
        self.message = f"{obj_name.title()} with ID {identifier} does not exist."
