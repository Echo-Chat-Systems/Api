"""
Contains the ConfigHandler.
"""

# Standard Library Imports

# Third Party Imports
from psycopg import AsyncCursor
from psycopg.sql import SQL
from psycopg.rows import DictRow

# Local Imports
from .base_handler import BaseHandler

# Constants
__all__ = [
    "ConfigHandler",
]


class ConfigHandler(BaseHandler):
    """
    Config handler.
    """
    async def get(
            self,
            key: str
    ) -> dict | None:
        """
        Get the configuration.

        Args:
            key (str): Key.

        Returns:
            dict: Configuration.
        """
        # Create a cursor
        cursor: AsyncCursor
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                SQL(
                    r"SELECT data FROM public.config WHERE key = %s;  /* Only select the unchanging columns, everything else is grabbed on-request */",
                ),
                [
                    key,
                ]
            )
            row: DictRow = await cursor.fetchone()

        if row is None:
            return None

        # Return
        return row["data"]