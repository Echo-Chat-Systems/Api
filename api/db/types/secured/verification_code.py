"""
Contains the verification code datatype
"""

# Standard Library Imports
from datetime import datetime
from uuid import UUID

# Third Party Imports
from psycopg import AsyncConnection
from psycopg.rows import DictRow
from psycopg.sql import Identifier

# Local Imports
from ..base_type import BaseType
from ..user import User
from ....models.secure import VerificationCode as VerificationCodeModel
from ....models.user import User as UserModel

# Constants
__all__ = [
    "VerificationCode",
]


class VerificationCode(BaseType):
    """
    Verification code datatype.
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
        super().__init__(connection, row, Identifier("secured", "verification_codes"))

    async def to_model(self) -> VerificationCodeModel:
        """
        Convert to model.

        Returns:
            VerificationCodeModel: Verification code model.
        """
        # Get user model
        user: User = await self.get_user()
        user_model: UserModel = await user.to_public()

        return VerificationCodeModel(
            id=self.id,
            created_at=self.created_at,
            user=user_model,
            code=await self.get_code(),
            expires=await self.get_expires(),
        )

    async def get_user_id(self) -> UUID:
        """
        Get user id.

        Returns:
            UUID: User id.
        """
        # Get user id
        row: DictRow = await self.id_get(
            column=Identifier("user_id"),
            id=self.id
        )
        return row["user_id"]

    async def get_user(self) -> User:
        """
        Get user.

        Returns:
            User: User.
        """
        # Get user
        user_id: UUID = await self.get_user_id()

        # Get user object
        user: User = await self.users.id_get(user_id)
        return user

    async def get_code(self) -> str:
        """
        Get code.

        Returns:
            str: Code.
        """
        # Get code
        row: DictRow = await self.id_get(
            column=Identifier("code"),
            id=self.id
        )
        return row["code"]

    async def get_expires(self) -> datetime:
        """
        Get expires.

        Returns:
            datetime: Expires.
        """
        # Get expires
        row: DictRow = await self.id_get(
            column=Identifier("expires"),
            id=self.id
        )
        return row["expires"]
