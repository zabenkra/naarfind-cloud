"""Multi-tenant query helpers — always scope data by organization."""

from sqlalchemy.orm import Query, Session, joinedload

from app.models.models import Device, FireEvent, Site


def devices_query(db: Session, organization_id: int) -> Query:
    return (
        db.query(Device)
        .join(Site, Device.site_id == Site.id)
        .filter(Site.organization_id == organization_id)
    )


def fire_events_query(db: Session, organization_id: int) -> Query:
    """Legacy tuple query (FireEvent, device_name) — prefer scoped_fire_events_query."""
    return (
        db.query(FireEvent, Device.name.label("device_name"))
        .join(Device, FireEvent.device_id == Device.id)
        .join(Site, Device.site_id == Site.id)
        .filter(Site.organization_id == organization_id)
    )


def scoped_fire_events_query(
    db: Session,
    organization_id: int | None,
) -> Query:
    """
    Organization-scoped FireEvent query used by both incident list and detail.
    - org user: inner join Device + Site, filter Site.organization_id
    - super_admin: all fire events (no org filter)
    """
    q = db.query(FireEvent).options(
        joinedload(FireEvent.device).joinedload(Device.site),
    )
    if organization_id is not None:
        q = (
            q.join(Device, FireEvent.device_id == Device.id)
            .join(Site, Device.site_id == Site.id)
            .filter(Site.organization_id == organization_id)
        )
    return q


def get_device_for_org(db: Session, device_id: int, organization_id: int) -> Device | None:
    return (
        devices_query(db, organization_id)
        .filter(Device.id == device_id)
        .first()
    )


def get_fire_event_for_org(db: Session, event_id: int, organization_id: int) -> FireEvent | None:
    return (
        scoped_fire_events_query(db, organization_id)
        .filter(FireEvent.id == event_id)
        .first()
    )
