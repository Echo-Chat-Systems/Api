"""
Contains the token datatype.
"""

# Standard Library Imports
from datetime import datetime
from uuid import UUID

# Third Party Imports
from psycopg.sql import Identifier
from psycopg import AsyncConnection
from psycopg.rows import DictRow

# Local Imports
from ..base_type import BaseType
from ....models.secure import Token as TokenModel, TokenTypes

# Constants
__all__ = [
    "Token",
]


class Token(BaseType):
    """
    Token datatype.
    """

    def __init__(
            self,
            connection: AsyncConnection,
            row: DictRow,
    ) -> None:
        """
        Initialize token.

        Args:
            connection: Connection.
            row: Row.
        """
        # Initialize BaseType
        super().__init__(connection, row, Identifier("secured", "tokens"))

    async def to_model(self) -> TokenModel:
        """
        Convert to model.

        Returns:
            TokenModel: Token model.
        """
        return TokenModel(
            id=self.id,
            created_at=self.created_at,
            user=await self.get_user_id(),
            last_used=await self.get_last_used(),
            type=await self.get_type(),
        )

    async def get_user_id(self) -> UUID:
        """
        Get user ID.

        Returns:
            UUID: User ID.
        """
        # Get user id
        row: DictRow = await self.id_get(
            column=Identifier("user_id"),
            id=self.id
        )
        return row["user_id"]

    async def get_last_used(self) -> datetime:
        """
        Get last used.

        Returns:
            datetime: Last used.
        """
        # Get last used
        row: DictRow = await self.id_get(
            column=Identifier("last_used"),
            id=self.id
        )
        return row["last_used"]

    async def get_type(self) -> TokenTypes:
        """
        Get type.

        Returns:
            int: Type.
        """
        # Get type
        row: DictRow = await self.id_get(
            column=Identifier("type"),
            id=self.id
        )
        return TokenTypes(row["type"])
