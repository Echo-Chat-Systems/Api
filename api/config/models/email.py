"""
Initializes the email module.
"""

# Standard Library Imports

# Third Party Imports
from dynaconf import Dynaconf

# Local Imports

# Constants
__all__ = [
    "CfEmail"
]


class CfEmail:
    """
    Email authentication configuration.
    """
    __slots__ = [
        "user",
        "password",
        "host",
        "port",
    ]

    def __init__(
            self,
            settings: Dynaconf
    ) -> None:
        """
        Initialises the Email object.
        """
        self.user: str = settings.email.user
        self.password: str = settings.email.password
        self.host: str = settings.email.host
        self.port: int = settings.email.port
