"""
Contains the base WS test endpoints.
"""
# Standard Library Imports
from unittest import IsolatedAsyncioTestCase

# Third Party Imports
from fastapi.testclient import TestClient

# Local Imports
from api.api import app

# Constants
__all__ = [
    "TestBase",
]


class TestBase(IsolatedAsyncioTestCase):
    """
    Test the base WS endpoints.
    """

    def test_connection(self) -> None:
        """
        Test that the application correctly handles a connection.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            pass

    def test_ping(self) -> None:
        """
        Test that the application correctly handles a ping.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            connection.send_json({"target": "ping"})
            assert connection.receive_json() == {"target": "pong"}

    def test_garbled_data(self) -> None:
        """
        Test that the application correctly handles garbled data.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            connection.send_bytes(b"garbled")
            assert connection.receive_json() == {"error": "Invalid data."}

    def test_no_data(self) -> None:
        """
        Test that the application correctly handles no data.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            connection.send_json({})
            assert connection.receive_json() == {"error": "No data provided."}

    def test_no_target_field(self) -> None:
        """
        Test that the application correctly handles no target.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            connection.send_json({"data": {}})
            assert connection.receive_json() == {"error": "No target provided or target invalid."}

    def test_empty_target_field(self) -> None:
        """
        Test that the application correctly handles an empty target.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            connection.send_json({"target": "", "data": {}})
            assert connection.receive_json() == {"error": "No target provided or target invalid."}

    def test_no_data_field(self) -> None:
        """
        Test that the application correctly handles no data.
        """
        # Create test client
        client: TestClient = TestClient(app)

        # Connect to the endpoint
        with client.websocket_connect("/") as connection:
            connection.send_json({"target": "test"})
            assert connection.receive_json() == {"error": "No action provided or target invalid."}

