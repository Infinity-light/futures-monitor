"""
---
role: Manage websocket clients and broadcast events.
depends:
  - typing.Any
  - asyncio
exports:
  - ConnectionHub
status: IMPLEMENTED
functions:
  - ConnectionHub.register(websocket: WebSocket) -> None
  - ConnectionHub.unregister(websocket: WebSocket) -> None
  - ConnectionHub.broadcast(message: dict) -> None
  - ConnectionHub.get_connection_count() -> int
---
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.websockets import WebSocket


logger = logging.getLogger(__name__)


class ConnectionHub:
    """WebSocket connection hub for broadcasting events to all connected clients."""

    def __init__(self) -> None:
        self._connections: set = set()
        self._lock = asyncio.Lock()

    async def register(self, websocket: WebSocket) -> None:
        """Register a new WebSocket connection."""
        async with self._lock:
            self._connections.add(websocket)
        logger.info(f"WebSocket registered. Total connections: {len(self._connections)}")

    async def unregister(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(f"WebSocket unregistered. Total connections: {len(self._connections)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected WebSocket clients."""
        if not self._connections:
            return

        disconnected = []
        for conn in list(self._connections):
            try:
                await conn.send_json(message)
            except Exception as exc:
                logger.warning(f"Failed to send message to WebSocket: {exc}")
                disconnected.append(conn)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self._connections.discard(conn)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


# Global singleton instance
_hub_instance: ConnectionHub | None = None


def get_hub() -> ConnectionHub:
    """Get the global ConnectionHub singleton instance."""
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = ConnectionHub()
    return _hub_instance
