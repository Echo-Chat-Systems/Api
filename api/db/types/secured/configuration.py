"""
Contains the configuration datatype.
"""
from uuid import UUID

# Standard Library Imports

# Third Party Imports
from psycopg import AsyncConnection
from psycopg.rows import DictRow
from psycopg.sql import Identifier

# Local Imports
from ..base_type import BaseType
from ....models.secure import UserConfig, TwoFactorMethods

# Constants
__all__ = [
    "UserConfiguration",
]


class UserConfiguration(BaseType):
    """
    User configuration datatype.
    """

    def __init__(
            self,
            connection: AsyncConnection,
            row: DictRow,
    ) -> None:
        """
        Initialize verification code.

        Args:
            connection (AsyncConnection): Connection.
            row (DictRow): Row.
        """
        # Initialize BaseType
        super().__init__(connection, row, Identifier("secured", "config"))

    async def to_model(self) -> UserConfig:
        """
        Convert to model.

        Returns:
            UserConfig: User configuration model.
        """
        return UserConfig(
            id=self.id,
            created_at=self.created_at,
            user_id=await self.get_user_id(),
            two_factor=await self.get_two_factor_method(),
        )

    async def get_user_id(self) -> UUID:
        """
        Get user id.

        Returns:
            UUID: User id.
        """
        row: DictRow = await self.id_get(
            column=Identifier("user_id"),
            id=self.id
        )
        return row["user_id"]

    async def get_two_factor_method(self) -> TwoFactorMethods:
        """
        Get two factor method.

        Returns:
            TwoFactorMethods: Two factor method.
        """
        row: DictRow = await self.id_get(
            column=Identifier("two_factor_method"),
            id=self.id
        )
        return TwoFactorMethods(row["two_factor_method"])

    async def set_two_factor_method(
            self,
            two_factor_method: TwoFactorMethods
    ) -> None:
        """
        Set two factor method.

        Args:
            two_factor_method (TwoFactorMethods): Two factor method.
        """
        await self.id_set(
            column=Identifier("two_factor_method"),
            id=self.id,
            value=two_factor_method.value
        )
