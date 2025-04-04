"""
Contains the admin WS test endpoints.
"""

# Standard Library Imports
from hashlib import md5
from random import randbytes
from unittest import IsolatedAsyncioTestCase

# Third Party Imports
from fastapi.testclient import TestClient
from rsa import decrypt
from starlette.testclient import WebSocketTestSession

# Local Imports
from api.api import app
from api.config import CONFIG
from api.tests.shared import add_user, admin_authenticate

# Constants
__all__ = [
    "TestAdmin"
]

def make_dict(action: str, data: dict) -> dict:
    """
    Make a dictionary with the action and data.
    """
    return {"target": "admin", "data": {"action": action, "data": data}}

class TestAdmin(IsolatedAsyncioTestCase):
    """
    Test the admin WS endpoints.
    """

    def test_admin_connect(self) -> None:
        """
        Test the admin WS connection.
        """
        # Create a test client
        client: TestClient = TestClient(app)

        # Make the request
        connection: WebSocketTestSession

        with client.websocket_connect("/admin/") as connection:
            return

    def test_admin_auth_success(self) -> None:
        """
        Tests the auth flow for admin connection with a successful auth attempt.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        connection: WebSocketTestSession
        with client.websocket_connect("/admin/") as connection:
            # Get the challenge
            challenge: bytes = connection.receive_bytes()

            # Decrypt challenge using private key
            challenge = decrypt(challenge, CONFIG.server.owner_private_key)

            # Hash the challenge
            response: bytes = md5(challenge).digest()

            # Reply with the response
            connection.send_bytes(response)

            # Check auth success
            assert connection.receive_json() == {"message": "Authenticated."}

    def test_admin_auth_fail(self) -> None:
        """
        Tests the auth flow for admin connection with a failed auth attempt.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        connection: WebSocketTestSession
        with client.websocket_connect("/admin/") as connection:
            # Get the challenge
            challenge: bytes = connection.receive_bytes()

            # Decrypt challenge using private key
            challenge = decrypt(challenge, CONFIG.server.owner_private_key)

            # Hash the challenge
            response: bytes = md5(challenge).digest()

            # Reply with the wrong response
            connection.send_bytes(response[::-1])

            # Check auth fail
            assert connection.receive_json() == {"message": "Authentication failed."}

    def test_admin_get_users_bad_data(self) -> None:
        """
        Test the admin WS get_users action raises bad data when no page info is provided.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        connection: WebSocketTestSession
        with client.websocket_connect("/admin/") as connection:
            # Authenticate
            admin_authenticate(connection)

            # Send bad data
            connection.send_json({""})

            # Check the response
            assert connection.receive_json() == {"error": "Invalid data."}

    def test_admin_get_users(self) -> None:
        """
        Test the admin WS get_users action.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        connection: WebSocketTestSession
        with client.websocket_connect("/admin/") as connection:
            # Authenticate
            admin_authenticate(connection)

            # Send get_users
            connection.send_json({"action": "get_users", "data": {"page": 0, "page_size": 1}})

            # Check the response
            data: dict = connection.receive_json()
            assert "data" in data
            assert isinstance(data["data"], list)
            assert len(data["data"]) == 1

    def test_admin_delete_user_bad_data(self) -> None:
        """
        Test the admin WS delete_user action raises bad data when no data is provided.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        connection: WebSocketTestSession
        with client.websocket_connect("/admin/") as connection:
            # Authenticate
            admin_authenticate(connection)

            # Send bad data
            connection.send_json({"action": "delete_user"})

            # Check the response
            assert connection.receive_json() == {"error": "Invalid data."}

    def test_admin_delete_user(self) -> None:
        """
        Test the admin WS delete_user action.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        connection: WebSocketTestSession
        with client.websocket_connect("/admin/") as connection:
            # Authenticate
            admin_authenticate(connection)

            # Build a new user
            user_data: dict = add_user("test_admin_delete_user")

            # Extract the user id
            user_id: str = user_data["data"]["id"]

            # Send delete_user
            connection.send_json({"action": "delete_user", "data": {"id": user_id}})

            # Check the response
            assert connection.receive_json() == {"action": "delete_user", "data": {"success": True}}
