"""
Contains all security related models
"""

# Standard Library Imports
from datetime import datetime
from enum import Enum
from uuid import UUID

# Third Party Imports
from pydantic import BaseModel

# Local Imports
from .base import BaseTableModel
from .user import User

# Constants
__all__ = [
    "Token",
    "Password",
]


class VerificationCode(BaseTableModel):
    """
    Verification code model.
    """
    user: User
    code: str
    expires: datetime


class TokenTypes(int, Enum):
    """
    Token types.
    """
    user: int = 1
    bot: int = 2


class Token(BaseTableModel):
    """
    Token model.
    """
    user: UUID
    last_used: datetime
    type: TokenTypes


class Password(BaseTableModel):
    """
    Password model.
    """
    hash: str
    last_updated: datetime


class PrivateUser(User):
    """
    Private user model.
    """
    tokens: list[Token]


class TwoFactorMethods(int, Enum):
    """
    Two factor methods.
    """
    email: int = 0
    totp: int = 1


class UserConfig(BaseTableModel):
    """
    User config model. Contains all the user's settings and configurations.
    """
    two_factor_method: TwoFactorMethods
