"""
Contains the base subworker.
"""

# Standard Library Imports

# Third Party Imports
from fastapi import WebSocket

# Local Imports
from api.db import Database

# Constants
__all__ = [
    "BaseSubworker"
]


class BaseSubworker:
    """
    Base subworker class.
    """
    connection: WebSocket
    database: Database

    def __init__(
            self,
            connection: WebSocket,
            database: Database
    ) -> None:
        """
        Initialise the worker.
        """
        self.connection = connection
        self.database = database


    async def handle_message(
            self,
            data: dict
    ) -> None:
        """
        Handle a message from the client.

        Args:
            data (dict): The data to handle.
        """
        raise NotImplementedError("Subclasses must implement this method.")

