"""
Contains the user routes.
"""
# Standard Library Imports
from datetime import datetime
from typing import Annotated

# Third Party Imports
from fastapi import APIRouter, Depends, WebSocket
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

# Local Imports
from ..db.database import Database
from ..db.exceptions.bases import DoesNotExist
from ..db.types.secured.verification_code import VerificationCode
from ..db.types.user import User
from ..models.user import User as UserModel


# Constants
__all__ = [
    "users_router",
]

from api.ws_workers.subworkers.users_worker import UsersWorker

# Create API router
users_router: APIRouter = APIRouter(
    prefix="/users",
    tags=["users"]
)


class CreateUserData(BaseModel):
    """
    Create user data model.
    """
    username: str
    email: str
    password: str


class LoginUserData(BaseModel):
    """
    Login user data model.
    """
    email: str
    password: str


@users_router.get("/verify/<verification_code>", tags=["users"])
async def verify_user(
        verification_code: str,
        database: Annotated[Database, Depends(Database.new)]
) -> UserModel:
    """
    Verifies a users email address.
    """
    # Get user
    try:
        code: VerificationCode = await database.secure.get_verification_code(verification_code)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Code not found")

    # Check if the validation code is expired
    if await code.get_expires() < datetime.now():
        await code.delete()
        raise HTTPException(status_code=403, detail="Validation code expired")

    # Get the user
    user: User = await code.get_user()

    # Update the user
    user.verified = True

    # Return user
    return await user.to_public()

# @users_router.post("/login", tags=["users"])
# async def login_user(
#         data: CreateUserData,
#         request: Request
# ) -> PyJWT:
#     """
#     Creates a new auth token for the user.
#     """
#     # Get database connection
#     db: Database = request.state.db
#
#     # Check if the user exists
#     user: User = await db.users.email_get(data.email)
#
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     # Get hashed password
#     password: Password = await db.secure.get_password(user.id)
#
#     # Check password
#     if not db.secure.verify_password(data.password, password.hash):
#         raise HTTPException(status_code=403, detail="Incorrect password")
#
#     # Build a new access token
#     token: Token = await db.secure.new_token(user.id)
#
#     # Encode token
#     return token.encode()
#
