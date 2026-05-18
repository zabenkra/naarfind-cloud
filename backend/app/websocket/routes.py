import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.deps import get_effective_organization_id
from app.core.security import decode_access_token, normalize_bearer_token
from app.models.models import User
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


def _org_id_from_token(token: str) -> int | None:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Token missing subject (sub)")

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(user_id), User.is_active.is_(True)).first()
        if not user:
            raise ValueError("User not found or inactive")
        return get_effective_organization_id(user)
    finally:
        db.close()


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    normalized = normalize_bearer_token(token)
    if not normalized:
        logger.warning("WebSocket rejected: missing token")
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        org_id = _org_id_from_token(normalized)
    except ExpiredSignatureError:
        logger.warning("WebSocket rejected: expired token")
        await websocket.close(code=1008, reason="Token expired")
        return
    except JWTError:
        logger.warning("WebSocket rejected: invalid token signature")
        await websocket.close(code=1008, reason="Invalid token")
        return
    except ValueError as exc:
        logger.warning("WebSocket rejected: %s", exc)
        await websocket.close(code=1008, reason="Invalid token")
        return

    await manager.connect(websocket, org_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        logger.debug("Client disconnected normally")
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
    finally:
        manager.disconnect(websocket)
