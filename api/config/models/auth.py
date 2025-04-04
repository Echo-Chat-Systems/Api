"""
Initializes the auth module.
"""

# Standard Library Imports

# Third Party Imports
from dynaconf import Dynaconf

# Local Imports

# Constants
__all__ = [
    "CfAuth"
]


class CfAuth:
    """
    Authentication configuration.
    """
    __slots__ = [
        "secret_key",
        "key_expires",
        "key_size",
        "fail_wait_time",
        "max_fail_attempts",
        "fail_lock_time",
        "admin_auth_timeout",
    ]

    def __init__(
            self,
            settings: Dynaconf
    ) -> None:
        """
        Initialises the Auth object.
        """
        self.secret_key = settings.auth.secret_key
        self.key_expires = settings.auth.key_expires
        self.key_size = settings.auth.key_size
        self.fail_wait_time = settings.auth.fail_wait_time
        self.max_fail_attempts = settings.auth.max_fail_attempts
        self.fail_lock_time = settings.auth.fail_lock_time
        self.admin_auth_timeout = settings.auth.admin_auth_timeout