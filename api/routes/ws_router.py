# Standard Library Imports
from typing import Annotated

# Third Party Imports
from fastapi import APIRouter, Depends, WebSocket

# Local Imports
from ..db.database import Database
from api.ws_workers import WsWorker

# Constants
__all__ = [

]

# Create API router
ws_router: APIRouter = APIRouter(
    prefix="/ws",
    tags=["ws"]
)


@ws_router.websocket("/")
async def ws_connect(
        websocket: WebSocket,
        database: Annotated[Database, Depends(Database.new)]
) -> None:
    """
    Route to establish a websocket connection.
    """
    await websocket.accept()

    # Pass off to the worker
    worker = WsWorker(websocket, database)
    await worker.run()
