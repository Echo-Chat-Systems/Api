"""
Initialises the tests module.
"""

# Standard Library Imports

# Third Party Imports

# Local Imports
from .tests_admin import TestAdmin
from .tests_users import TestUsers

# Constants
__all__ = [
    "TestAdmin",
    "TestUsers",
]
