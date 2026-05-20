from sqlalchemy.orm import Session

from app.models.models import Device, FireEvent, Site
from app.services.device_serializer import device_to_out
from app.services.fire_events import to_fire_event_out
from app.websocket.manager import manager


def _organization_id_for_device(db: Session, device: Device | None) -> int | None:
    if not device or not device.site_id:
        return None
    site = db.query(Site).filter(Site.id == device.site_id).first()
    return site.organization_id if site else None


async def broadcast_fire_event(
    event: FireEvent,
    device: Device | None,
    db: Session,
) -> None:
    device_name = device.name if device else None
    event_out = to_fire_event_out(event, device_name)
    org_id = _organization_id_for_device(db, device)

    await manager.broadcast_json(
        {
            "type": "fire_event",
            "event": event_out.model_dump(mode="json"),
        },
        organization_id=org_id,
    )


async def broadcast_device_heartbeat(
    device: Device,
    db: Session,
) -> None:
    site_name = None
    if device.site_id:
        site = db.query(Site).filter(Site.id == device.site_id).first()
        site_name = site.name if site else None

    device_out = device_to_out(device, site_name)
    org_id = _organization_id_for_device(db, device)

    await manager.broadcast_json(
        {
            "type": "device_heartbeat",
            "device": device_out.model_dump(mode="json"),
        },
        organization_id=org_id,
    )
