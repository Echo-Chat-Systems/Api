"""
Contains the user WS test endpoints.
"""

# Standard Library Imports
from datetime import datetime
from random import randbytes
from unittest import IsolatedAsyncioTestCase
from uuid import UUID

# Third Party Imports
from fastapi.responses import Response
from fastapi.testclient import TestClient

# Local Imports
from api.api import app
from api.tests.shared import add_user

# Constants
__all__ = [
    "TestUsers",
]

def make_dict(action: str, data: dict) -> dict:
    """
    Make a dictionary with the action and data.
    """
    return {"target": "users", "data": {"action": action, "data": data}}

class TestUsers(IsolatedAsyncioTestCase):
    """
    Test the user WS endpoints.
    """

    def test_user_new_valid(self) -> None:
        """
        Test that a new valid user can be created.
        """
        response: dict = add_user("test_user_new_valid")

        assert response.get("action") == "new"
        data: dict = response.get("data")
        assert data.get("id") is not None
        UUID(data.get("id"))  # Try and trigger a UUID conversion error
        assert data.get("created_at") is not None
        datetime.strptime(data.get("created_at"), "%Y-%m-%dT%H:%M:%S.%f")
        assert data.get("email") is not None
        assert data.get("username") is not None
        assert data.get("icon") is None
        assert data.get("bio") is None
        assert data.get("status") == {"type": 0, "text": ""}
        assert data.get("last_online") is not None
        datetime.strptime(data.get("last_online"), "%Y-%m-%dT%H:%M:%S.%f")
        assert data.get("is_online") is False
        assert data.get("is_banned") is False
        assert data.get("is_verified") is False

    def test_email_validator_fake_code(self) -> None:
        """
        Tests the email validation system with a fake code.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Generate a fake verification code
        fake_code: str = "fake_code"

        # Fire off the fake code into the /users/verify/ endpoint
        response: Response = client.get(f"/users/verify/{fake_code}")

        # Check that the user is not verified
        assert response.status_code == 404

    def test_email_validator_real_code(self) -> None:
        """
        It is not possible to test the email validation system completely automatically, as it requires the ability to read emails, which is massively out of scope for a
        unittest.
        """

    def test_email_validator_garbled_data(self) -> None:
        """
        Test that the application correctly validates the passed data by sending a garbled message.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        response: Response = client.get("/users/verify/".join(str(randbytes(100))))
        assert response.status_code == 404
