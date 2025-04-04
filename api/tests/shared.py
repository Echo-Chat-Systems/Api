"""
Contains shared objects for testing.
"""

# Standard Library Imports
from hashlib import md5
from uuid import UUID, uuid4
from typing import Literal
from random import choice as random_choice
from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits, punctuation, printable

# Third Party Imports
from fastapi.testclient import TestClient
from rsa import decrypt
from starlette.testclient import WebSocketTestSession
from starlette.websockets import WebSocketDisconnect

# Local Imports
from api.config import CONFIG
from api import app

# Constants
__all__ = [
    "admin_authenticate",
    "generate_password",
    "add_user",
]


def admin_authenticate(
        connection: WebSocketTestSession
) -> WebSocketTestSession:
    """
    Authenticates a connection to an admin WS endpoint.
    """
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

    return connection


def generate_password(
        num_lowercase: int,
        num_uppercase: int,
        num_number: int,
        num_special: int,
        length: int,
        padding_type: Literal["lower", "upper", "number", "special", "random"] = "random"
) -> str:  # TODO: Make this include all possible characters including random bytes
    """
    Generates a password with the given requirements.

    Args:
        num_lowercase (int): The number of lowercase characters to include.
        num_uppercase (int): The number of uppercase characters to include.
        num_number (int): The number of number characters to include.
        num_special (int): The number of special characters to include.
        length (int): The length of the password.
        padding_type (Literal["lower", "upper", "number", "special", "random"]): The padding to use.

    Returns:
        str: The generated password.
    """
    # Check that the individual requirements are not greater than the total length
    if num_lowercase + num_uppercase + num_number + num_special > length:
        raise ValueError("The sum of the individual requirements must be less than the total length.")

    # Generate the password
    password: str = (
        f"{random_choice(ascii_lowercase) * num_lowercase}"
        f"{random_choice(ascii_uppercase) * num_uppercase}"
        f"{random_choice(digits) * num_number}"
        f"{random_choice(punctuation) * num_special}"
    )

    # Genre the padding
    padding: str

    if padding_type == "lower":
        padding = random_choice(ascii_letters.lower())
    elif padding_type == "upper":
        padding = random_choice(ascii_letters.upper())
    elif padding_type == "number":
        padding = random_choice(digits)
    elif padding_type == "special":
        padding = random_choice(punctuation)
    elif padding_type == "random":
        padding = random_choice(printable)
    else:
        raise ValueError("Invalid padding type.")

    # Pad the password with the given padding
    for _ in range(length - len(password)):
        password += random_choice(padding)

    # Return the password
    return password


def add_user(
        test_name: str
) -> dict:
    """
    Adds a valid user.

    Returns:
        dict: The user data.
    """
    # Create test client
    client: TestClient = TestClient(app)

    # Connect to the endpoint
    try:
        with client.websocket_connect("/") as connection:
            # Generate the user data
            test_user_id: UUID = uuid4()
            password: str = generate_password(
                num_lowercase=CONFIG.user_security.password_require_lowercase,
                num_uppercase=CONFIG.user_security.password_require_uppercase,
                num_number=CONFIG.user_security.password_require_number,
                num_special=CONFIG.user_security.password_require_special_character,
                length=100,
                padding_type="random"
            )
            # Submit the user data
            user_data: dict = {
                "target": "users",
                "data": {
                    "action": "new",
                    "data": {
                        "username": f"{test_name}-{test_user_id}",
                        "email": f"{test_name}-{test_user_id}@dafox.au",
                        "password": password
                    }
                }
            }

            connection.send_json(user_data)

            # Print the response
            data: dict = connection.receive_json()

            # Check the response
            assert data["action"] == "new"
            assert data["data"]["email"] == user_data["data"]["email"]
            assert data["data"]["username"] == user_data["data"]["username"]
            assert data["data"]["icon"] is None
            assert data["data"]["bio"] is None
            assert data["data"]["status"] == {"type": 0, "text": ""}
            assert data["data"]["is_online"] is False
            assert data["data"]["is_banned"] is False
            assert data["data"]["is_verified"] is False

            # Try converting the UUID
            try:
                UUID(data["data"]["id"])
            except ValueError:
                assert False

            # Return the user data
            return data
    except WebSocketDisconnect as e:
        print(e.reason)
        raise e
