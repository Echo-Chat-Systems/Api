"""
Main file for API.
"""
# Standard Library Imports
from sys import platform
from typing import Callable

# Third Party Imports
from fastapi import APIRouter, FastAPI, Request
from fastapi.security import OAuth2PasswordBearer

# Local Imports
from .routes import *

# Constants
__all__ = [
    "app",
    "create_app",
]

from .routes.ws_router import ws_router

# Set event loop policy for Windows because of async weirdness
if platform == "win32":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy  # These imports are here because they don't exist on anything but windows

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())


def create_app(
        extensions: list[APIRouter] = None,
        middleware: list[Callable] = None
) -> FastAPI:
    """
    Create FastAPI instance.
    """
    # Create FastAPI instance
    api: FastAPI = FastAPI()

    # Register routes
    api.include_router(api_router)  # Base url
    api.include_router(ws_router)  # Websocket routes
    api.include_router(users_router)  # User routes
    api.include_router(administrator_router)  # Admin routes

    # Register extensions
    if extensions:
        for extension in extensions:
            api.include_router(extension)

    # Register middleware
    if middleware:
        for middleware_item in middleware:
            api.add_middleware(middleware_item)

    # Set token url
    ouath2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

    return api


# Create app
app: FastAPI = create_app()
