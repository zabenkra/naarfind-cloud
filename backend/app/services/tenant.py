"""Multi-tenant query helpers — always scope data by organization."""

from sqlalchemy.orm import Query, Session

from app.models.models import Device, FireEvent, Site


def devices_query(db: Session, organization_id: int) -> Query:
    return (
        db.query(Device)
        .join(Site, Device.site_id == Site.id)
        .filter(Site.organization_id == organization_id)
    )


def fire_events_query(db: Session, organization_id: int) -> Query:
    return (
        db.query(FireEvent, Device.name.label("device_name"))
        .join(Device, FireEvent.device_id == Device.id)
        .join(Site, Device.site_id == Site.id)
        .filter(Site.organization_id == organization_id)
    )


def get_device_for_org(db: Session, device_id: int, organization_id: int) -> Device | None:
    return (
        devices_query(db, organization_id)
        .filter(Device.id == device_id)
        .first()
    )


def get_fire_event_for_org(db: Session, event_id: int, organization_id: int) -> FireEvent | None:
    row = (
        fire_events_query(db, organization_id)
        .filter(FireEvent.id == event_id)
        .first()
    )
    return row[0] if row else None
