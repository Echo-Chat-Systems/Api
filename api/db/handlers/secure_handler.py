"""
Contains the secure handler.
"""
# Standard Library Imports
from datetime import datetime, timedelta
from uuid import UUID
from secrets import token_urlsafe

# Third Party Imports
from psycopg import AsyncCursor
from psycopg.rows import DictRow
from psycopg.sql import SQL

# Local Imports
from ..exceptions.bases import DoesNotExist
from .base_handler import BaseHandler
from ..types.secured.configuration import UserConfiguration
from ..types.secured.token import Token
from ..types.secured.verification_code import VerificationCode
from ...config import CONFIG
from ...models.secure import Password
from ...security.scheme import crypt_context

# Constants
__all__ = [
    "SecureHandler",
]


class SecureHandler(BaseHandler):
    """
    Secure handler.
    """

    @staticmethod
    def hash_password(
            password: str
    ) -> str:
        """
        Hash a password.

        Args:
            password (str): Password.

        Returns:
            str: Hashed password.
        """
        return crypt_context.hash(password)

    @staticmethod
    def verify_password(
            password: str,
            hashed_password: str
    ) -> bool:
        """
        Verify a password.

        Args:
            password (str): Password.
            hashed_password (str): Hashed password.

        Returns:
            bool: Verification.
        """
        return crypt_context.verify(password, hashed_password)

    async def set_password(
            self,
            user_id: UUID,
            password: str
    ) -> None:
        """
        Sets a user's password.

        Args:
            user_id (UUID): User ID.
            password (str): Password.
        """

        # Hash password
        password: str = self.hash_password(password)  # Overwrite password with hashed password

        # Get cursor
        cursor: AsyncCursor
        async with self.connection.cursor() as cursor:
            # Remove old password
            await cursor.execute(
                SQL(
                    r"DELETE FROM secured.passwords WHERE user_id = %s;",
                ),
                [
                    user_id,
                ]
            )

            # Insert new password
            await cursor.execute(
                SQL(
                    r"INSERT INTO secured.passwords (user_id, hash) VALUES (%s, %s);",
                ),
                [
                    user_id,
                    password,
                ]
            )

    async def get_password(
            self,
            user_id: UUID
    ) -> Password | None:
        """
        Gets the hash of a user's password from the database.

        Args:
            user_id (UUID): User ID.

        Returns:
            str: Hashed password.
        """
        cursor: AsyncCursor
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                SQL(
                    r"SELECT hash, last_updated FROM secured.passwords WHERE user_id = %s;",
                ),
                [
                    user_id,
                ]
            )
            row: dict = await cursor.fetchone()

        if row is None:
            return None

        return Password(
            hash=row["password"],
            last_updated=row["last_updated"]
        )

    async def new_token(
            self,
            user_id: UUID,
            token_type: int = 0
    ) -> Token:
        """
        Build a new authentication token.

        Args:
            user_id (UUID): User ID.
            token_type (int): Token type. Defaults to a User token.

        Returns:
            Token: Token.
        """
        # Get cursor
        cursor: AsyncCursor
        async with self.connection.cursor() as cursor:
            # Insert new token
            cursor: AsyncCursor = await cursor.execute(
                SQL(
                    r"INSERT INTO secured.tokens (user_id, type) VALUES (%s, %s) RETURNING id, created_at;",
                ),
                [
                    user_id,
                    token_type,
                ]
            )

            row: DictRow = await cursor.fetchone()

        return Token(
            self.connection,
            row
        )

    async def exists_token(
            self,
            token_id: UUID
    ) -> bool:
        """
        Checks if a token is found in the database.

        Args:
            token_id (UUID): Token ID.

        Returns:
            bool: Token exists.
        """
        # Check if token exists
        async with self.connection.cursor() as cursor:
            cursor: AsyncCursor

            # Check if token exists
            await cursor.execute(
                "SELECT 1 FROM secured.tokens WHERE id = %s;",
                [str(token_id)]
            )

            return bool(await cursor.fetchone())


    async def get_token(
            self,
            token_id: UUID
    ) -> Token:
        """
        Get a token by ID.

        Args:
            token_id (UUID): Token ID.

        Returns:
            Token: Token.
        """
        # Check if token exists
        if not await self.exists_token(token_id):
            raise DoesNotExist("Token", "secured.tokens", token_id)
        # Get token
        async with self.connection.cursor() as cursor:
            cursor: AsyncCursor

            # Get token
            await cursor.execute(
                "SELECT * FROM secured.tokens WHERE id = %s;",
                [str(token_id)]
            )

            token_data: DictRow = await cursor.fetchone()

        return Token(
            self.connection,
            token_data
        )

    async def get_tokens(
            self,
            user_id: UUID
    ) -> list[Token]:
        """
        Gets the tokens of a user.

        Args:
            user_id (UUID): User ID.

        Returns:
            list[str]: Tokens.
        """
        # Get tokens
        async with self.connection.cursor() as cursor:
            cursor: AsyncCursor

            # Get tokens
            await cursor.execute(
                "SELECT * FROM secured.tokens WHERE user_id = %s;",
                [str(user_id)]
            )

            token_data: list[DictRow] = await cursor.fetchall()

        return [
            Token(
                self.connection,
                token
            ) for token in token_data
        ]

    async def make_verification_code(
            self,
            user_id: UUID
    ) -> VerificationCode:
        """
        Creates a new verification code for a user.

        Args:
            user_id (UUID): User id to add code for.

        Returns:
            VerificationCode: The newly created code for the user.
        """

        # Calculate expiry
        expires: datetime = datetime.now() + timedelta(
            days=CONFIG.user_security.verification_expires_days,
            hours=CONFIG.user_security.verification_expires_hours
        )

        # Get cursor
        cursor: AsyncCursor
        async with self.connection.cursor() as cursor:
            while 1:  # Check if the code already exists
                # Generate a 256 character long random string
                code: str = token_urlsafe(256)

                # Check if the code already exists
                await cursor.execute(
                    SQL(
                        r"SELECT * FROM secured.verification_codes WHERE user_id = %s;",
                    ),
                    [
                        user_id,
                    ]
                )

                if not await cursor.fetchone():  # If the code does not exist, break
                    break

            # Remove old code
            await cursor.execute(
                SQL(
                    r"DELETE FROM secured.verification_codes WHERE user_id = %s;"  # This is causing the table to be wiped for some reason.
                ),
                [
                    user_id,
                ]
            )

            # Insert new code
            cursor: AsyncCursor = await cursor.execute(
                SQL(
                    r"INSERT INTO secured.verification_codes (user_id, code, expires) VALUES (%s, %s, %s) RETURNING id, created_at;",
                ),
                [
                    user_id,
                    code,
                    expires
                ]
            )

            row: DictRow = await cursor.fetchone()

        return VerificationCode(
            self.connection,
            row
        )

    async def get_verification_code(
            self,
            validation_token: str
    ) -> VerificationCode:
        """
        Gets a verification code.

        Args:
            validation_token (str): Validation token.

        Returns:
            VerificationCode: Verification code.
        """
        # Get verification code
        async with self.connection.cursor() as cursor:
            cursor: AsyncCursor

            # Get verification code
            await cursor.execute(
                "SELECT * FROM secured.verification_codes WHERE code = %s;",
                [validation_token]
            )

            verification_code_data: DictRow = await cursor.fetchone()

        return VerificationCode(
            self.connection,
            verification_code_data
        )

    async def make_config(
            self,
            user_id: UUID
    ) -> None:
        """
        Make a user configuration.

        Args:
            user_id (UUID): User ID.
        """
        # Get cursor
        cursor: AsyncCursor
        async with self.connection.cursor() as cursor:
            # Insert new configuration
            await cursor.execute(
                SQL(
                    r"INSERT INTO secured.config (user_id) VALUES (%s);",
                ),
                [
                    user_id,
                ]
            )

    async def get_config(
            self,
            user_id: UUID
    ) -> UserConfiguration:
        """
        Gets a user's configuration.

        Args:
            user_id (UUID): User ID.

        Returns:
            UserConfiguration: User configuration.
        """
        # Get user configuration
        async with self.connection.cursor() as cursor:
            cursor: AsyncCursor

            # Get user configuration
            await cursor.execute(
                "SELECT * FROM secured.config WHERE user_id = %s;",
                [user_id]
            )

            user_config_data: DictRow = await cursor.fetchone()

        return UserConfiguration(
            self.connection,
            user_config_data
        )
