import json
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class ClientConnection:
    websocket: WebSocket
    organization_id: int | None  # None = super_admin (receives all orgs)


class ConnectionManager:
    """Manages WebSocket connections scoped by organization."""

    def __init__(self) -> None:
        self.active_connections: list[ClientConnection] = []

    async def connect(self, websocket: WebSocket, organization_id: int | None) -> None:
        await websocket.accept()
        self.active_connections.append(
            ClientConnection(websocket=websocket, organization_id=organization_id)
        )
        logger.info(
            "WebSocket connected org_id=%s (%d clients)",
            organization_id,
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections = [
            c for c in self.active_connections if c.websocket is not websocket
        ]
        logger.info("WebSocket disconnected (%d clients)", len(self.active_connections))

    async def broadcast_json(
        self,
        data: dict[str, Any],
        organization_id: int | None = None,
    ) -> None:
        if not self.active_connections:
            return

        message = json.dumps(data, default=str)
        dead: list[WebSocket] = []

        for client in list(self.active_connections):
            if organization_id is not None:
                if client.organization_id is not None and client.organization_id != organization_id:
                    continue

            try:
                await client.websocket.send_text(message)
            except (WebSocketDisconnect, RuntimeError, Exception) as exc:
                logger.warning("WebSocket send failed: %s", exc)
                dead.append(client.websocket)

        for websocket in dead:
            self.disconnect(websocket)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()
