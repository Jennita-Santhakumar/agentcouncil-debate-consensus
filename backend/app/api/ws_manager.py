"""In-process WebSocket connection manager, keyed by debate id.

No Redis is needed: a debate is orchestrated entirely within one backend
process (a single background asyncio task), so an in-memory
`dict[str, list[WebSocket]]` is sufficient to fan out round updates to every
client watching that debate. This would need to change to a pub/sub backend
(e.g. Redis) only if the API were horizontally scaled across processes.
"""
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, debate_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(debate_id, []).append(websocket)

    def disconnect(self, debate_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(debate_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns and debate_id in self._connections:
            del self._connections[debate_id]

    async def broadcast(self, debate_id: str, message: dict) -> None:
        for ws in list(self._connections.get(debate_id, [])):
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send to a websocket client for debate %s: %s", debate_id, exc)
                self.disconnect(debate_id, ws)


manager = ConnectionManager()
