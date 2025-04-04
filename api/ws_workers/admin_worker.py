"""
Contains the WS Admin Worker.
"""

# Standard Library Imports
from datetime import datetime, timedelta
from hashlib import md5
from secrets import token_bytes

# Third Party Imports
from pydantic import ValidationError
from fastapi import WebSocket
from rsa import encrypt
from starlette.websockets import WebSocketDisconnect

from .subworkers.base_subworker import BaseSubworker
# Local Imports
from .ws_worker import WsWorker
from ..config import CONFIG
from ..db.exceptions import UserDoesNotExist
from ..db.types.user import User
from ..models.user import User as PublicUser
from ..models.validation.admin import DeleteUserInput, GetUsersInput

# Constants
__all__ = [
    "AdminWorker",
]

# Store currently authenticated admins and their expiry times
admins: dict[WebSocket, datetime] = {}

# Dictionary of clients that have failed authentication and the times they can try again. This is to prevent brute force attacks.
# The reason that there is a list of datetimes is to store the number of times that the client has failed authentication.
waitlist: dict[WebSocket, list[datetime]] = {}

class AdminWorker(BaseSubworker):
    """
    Worker to handle admin WebSocket connections.
    """

    async def handle_message(
            self,
            data: dict
    ) -> None:
        """
        Handle a message from the client.

        Args:
            data (dict): The data to handle.
        """
        # Match action
        action: str = data.get("action")

        match action:
            case "auth":
                await self._auth(data)
            case "logoff":
                await self._logoff(data)
            case "get_users":
                await self._get_users(data)
            case "get_user":
                await self._get_user(data)
            case "delete_user":
                await self._delete_user(data)
            case _:
                await self.connection.send_json(
                    {"error": "Invalid action."}
                )

    async def _auth(
            self,
            data: dict
    ) -> None:
        """
        Authenticate an admin.

        Args:
            data (dict): Data.
        """
        # Verify input model

        # Check if the client is in the waitlist  TODO: Make a test for this
        if self.connection in waitlist:
            # Check if the client can try again
            if datetime.now() < waitlist[self.connection][max(len(waitlist[self.connection]) - 1, 0)]:
                await self.connection.send_json(
                    {"error": "You must wait before trying again."}
                )
                return

        # Generate a token for the connection
        token: bytes = token_bytes(32)

        # Encrypt the token using the public key
        encrypted_token: bytes = encrypt(token, CONFIG.server.owner_public_key)

        # Send the token to the client
        await self.connection.send_bytes(encrypted_token)

        # Calculate the expected token
        client_expected: bytes = md5(token).digest()

        # Receive the token back from the client
        try:
            client_actual: bytes = await self.connection.receive_bytes()  # This is causing an error
        except WebSocketDisconnect:
            return  # Gracefully handle disconnect

        # Check if the response is exactly what was expected (Yes I know this is ugly)
        if client_actual != client_expected:  # Check if the response is exactly what was expected

            await self.connection.send_json({"target": "admin", "data": {"message": "Authentication failed."}})

            # Add the client to the waitlist
            if self.connection in waitlist:
                # Check if the client has failed authentication too many times
                if len(waitlist[self.connection]) >= CONFIG.auth.max_fail_attempts:
                    waitlist[self.connection].append(datetime.now() + timedelta(seconds=CONFIG.auth.fail_lock_time))
                else:
                    waitlist[self.connection].append(datetime.now() + timedelta(seconds=CONFIG.auth.fail_timeout))

            else:
                waitlist[self.connection] = [datetime.now() + timedelta(seconds=CONFIG.auth.fail_timeout)]
            return

        # Send the client a message to say that they are authenticated
        admins[self.connection] = datetime.now() + timedelta(seconds=CONFIG.auth.admin_auth_timeout)
        await self.connection.send_json(
            {"message": "Authenticated."}
        )

    async def _logoff(
            self,
            data: dict
    ) -> None:
        """
        Log off an admin.

        Args:
            data (dict): Data.
        """
        # Verify input model

        # Check if the client is authenticated
        if self.connection not in admins:
            await self.connection.send_json(
                {"error": "Not authenticated."}
            )
            return

        # Remove the client from the authenticated list
        del admins[self.connection]
        del waitlist[self.connection]

        # Send success
        await self.connection.send_json(
            {
                "action": "logoff",
                "data": {"success": True}
            }
        )

    async def _get_users(
            self,
            data: dict
    ) -> None:
        """
        Get users.

        Args:
            data (dict): Data.
        """
        # Verify input model
        try:
            data: GetUsersInput = GetUsersInput(**data)
        except ValidationError:
            await self.connection.send_json(
                {"error": "Invalid data."}
            )
            return

        # Get users
        users: list[User] = await self.database.users.get(
            data.data.page,
            data.data.page_size
        )
        users: list[PublicUser] = [await user.to_public() for user in users]

        # Send users
        await self.connection.send_json(
            {
                "action": "users",
                "data": [user.model_dump(mode="json") for user in users]
            }
        )

    async def _get_user(
            self,
            data: dict
    ) -> None:
        """
        Get a user.

        Args:
            data (dict): Data.
        """

    async def _delete_user(
            self,
            data: dict
    ) -> None:
        """
        Delete a user.

        Args:
            data (dict): Data.
        """
        # Verify input model
        try:
            data: DeleteUserInput = DeleteUserInput(**data)
        except ValidationError:
            await self.connection.send_json(
                {"error": "Invalid data."}
            )
            return

        # Delete user
        try:
            await self.database.users.delete(
                data.data.id
            )
        except UserDoesNotExist:
            await self.connection.send_json(
                {"error": "User does not exist."}
            )
            return

        # Send success
        await self.connection.send_json(
            {
                "action": "delete_user",
                "data": {"success": True}
            }
        )
