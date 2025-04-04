"""
Contains the base worker.
"""
from typing import Callable

# Standard Library Imports

# Third Party Imports
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

# Local Imports
from ..db import Database
from .subworkers.base_subworker import BaseSubworker
from .subworkers import UsersWorker

# Constants
__all__ = [
    "WsWorker",
]


def verify_field(data: dict, field: str, field_type: type) -> bool:
    """
    Verify that a field is present and of the correct type.

    Args:
        data (dict): The data to check.
        field (str): The field to check.
        field_type (type): The type the field should be.

    Returns:
        bool: True if the field is present and of the correct type, False otherwise.
    """
    if field not in data:
        return False

    if data[field] is None:
        return False

    if not isinstance(data[field], field_type):
        return False

    return True

class WsWorker:
    """
    Base worker class.
    """
    connection: WebSocket
    database: Database

    workers: dict[str, Callable[[WebSocket, Database], BaseSubworker]] = {
        "users": UsersWorker
    }

    def __init__(
            self,
            connection: WebSocket,
            database: Database
    ) -> None:
        """
        Initialise the worker.
        """
        self.connection = connection
        self.database = database

        for worker in self.workers.values():
            worker(connection, database)

    async def run(self) -> None:
        """
        Run the worker.

        Starts the event handle loop for the worker and listens for incoming messages. When an incoming message is received, this method fires a callback to `handle_message`.
        """
        while True:
            try:
                content: dict = await self.connection.receive_json()
            except WebSocketDisconnect:
                await self.connection.close()
                return
            except KeyError:  # This catches the error when the data is not a dictionary.
                await self.connection.send_json(
                    {
                        "error": "Invalid data."
                    }
                )
                continue

            # Check required fields are present, not null, and are the correct type
            if content == {}:
                await self.connection.send_json(
                    {
                        "error": "No data provided."
                    }
                )
                continue

            if not verify_field(content, "target", str):
                await self.connection.send_json(
                    {
                        "error": "No target provided or target invalid."
                    }
                )
                continue

            if not verify_field(content, "data", dict):
                await self.connection.send_json(
                    {
                        "error": "No data provided or data invalid."
                    }
                )
                continue

            if content["target"] == "ping":
                await self.connection.send_json(
                    {
                        "target": "pong"
                    }
                )
                continue

            # Now that we know that the first level of the message is well-formatted, we de-encapsulate the data field and verify again
            data: dict = content["data"]

            if not verify_field(data, "action", str):
                await self.connection.send_json(
                    {
                        "error": "No action provided or action invalid."
                    }
                )
                continue

            if not verify_field(data, "data", dict):
                await self.connection.send_json(
                    {
                        "error": "No data provided or data invalid."
                    }
                )
                continue

            await self.direct_message(content["target"], data)

    async def direct_message(self, target: str, data: dict) -> None:
        """
        Direct a message to a target.

        Args:
            target (str): The target of the message.
            data (dict): The data to send.
        """
        if target not in self.workers:
            await self.connection.send_json(
                {
                    "error": "Target not found."
                }
            )
            return

        await self.workers[target].handle_message(data)
