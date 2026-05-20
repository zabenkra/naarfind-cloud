import json
import logging
from typing import Any, Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_effective_organization_id
from app.models.models import AuditLog, Device, FireEvent, IncidentNote, Site, User
from app.schemas.incidents import (
    IncidentDetailOut,
    IncidentDeviceOut,
    IncidentListItemOut,
    IncidentNoteOut,
    IncidentSiteOut,
    TimelineEntry,
)
from app.services.tenant import scoped_fire_events_query

logger = logging.getLogger(__name__)

INCIDENT_NOT_FOUND_MSG = "Incident not found for this organization"


def _parse_metadata(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def _incident_not_found_detail(
    requested_id: int,
    *,
    reason: str,
    organization_id: int | None,
) -> dict[str, Any]:
    return {
        "detail": INCIDENT_NOT_FOUND_MSG,
        "requested_id": requested_id,
        "reason": reason,
        "organization_id": organization_id,
    }


def raise_incident_not_found(
    requested_id: int,
    *,
    reason: str,
    organization_id: int | None,
) -> None:
    logger.info(
        "incident_detail not_found requested_id=%s reason=%s organization_id=%s",
        requested_id,
        reason,
        organization_id,
    )
    raise HTTPException(
        status_code=404,
        detail=_incident_not_found_detail(
            requested_id,
            reason=reason,
            organization_id=organization_id,
        ),
    )


def resolve_fire_event_for_incident(
    db: Session,
    requested_id: int,
    organization_id: int | None,
) -> tuple[FireEvent, Literal["fire_event_id", "incident_note_id"]]:
    """
    Resolve incident id to a FireEvent using the same org scope as list.
    1) FireEvent.id == requested_id (primary)
    2) IncidentNote.id == requested_id → use note.incident_id (compatibility)
    """
    scoped = scoped_fire_events_query(db, organization_id)

    event = scoped.filter(FireEvent.id == requested_id).first()
    if event:
        logger.info(
            "incident_detail resolved requested_id=%s via=fire_event_id organization_id=%s fire_event_id=%s",
            requested_id,
            organization_id,
            event.id,
        )
        return event, "fire_event_id"

    note = (
        db.query(IncidentNote)
        .filter(IncidentNote.id == requested_id)
        .first()
    )
    if note:
        event = scoped.filter(FireEvent.id == note.incident_id).first()
        if event:
            logger.info(
                "incident_detail resolved requested_id=%s via=incident_note_id organization_id=%s fire_event_id=%s",
                requested_id,
                organization_id,
                event.id,
            )
            return event, "incident_note_id"

    exists = db.query(FireEvent.id).filter(FireEvent.id == requested_id).first()
    if not exists and note:
        exists = db.query(FireEvent.id).filter(FireEvent.id == note.incident_id).first()

    if not exists:
        raise_incident_not_found(
            requested_id,
            reason="fire_event_not_found",
            organization_id=organization_id,
        )
    raise_incident_not_found(
        requested_id,
        reason="organization_scope_mismatch",
        organization_id=organization_id,
    )


def get_incident_context(
    db: Session,
    incident_id: int,
    organization_id: int | None,
) -> tuple[FireEvent, Device | None, Site | None]:
    """Load fire event using the same scoped query as list_incidents."""
    logger.info(
        "incident_detail lookup requested_id=%s organization_id=%s",
        incident_id,
        organization_id,
    )
    event, _ = resolve_fire_event_for_incident(db, incident_id, organization_id)
    device = event.device
    site = device.site if device else None
    return event, device, site


def get_incident_row(
    db: Session,
    incident_id: int,
    organization_id: int | None,
) -> tuple[FireEvent, str | None, str | None]:
    event, device, site = get_incident_context(db, incident_id, organization_id)
    return event, device.name if device else None, site.name if site else None


def build_timeline(
    event: FireEvent,
    notes: list[IncidentNote],
    audit_entries: list[AuditLog],
) -> list[TimelineEntry]:
    items: list[TimelineEntry] = []

    if event.created_at:
        items.append(
            TimelineEntry(
                id=f"created-{event.id}",
                type="created",
                action="incident_opened",
                message="Fire incident detected and logged",
                created_at=event.created_at,
            )
        )

    for entry in audit_entries:
        meta = _parse_metadata(entry.metadata_json)
        user_name = entry.user.full_name if entry.user else None
        message = None
        if entry.action == "status_changed" and meta:
            message = f"Status changed to {meta.get('new_status', '')}"
        items.append(
            TimelineEntry(
                id=f"audit-{entry.id}",
                type="audit",
                action=entry.action,
                message=message,
                user_name=user_name,
                metadata=meta,
                created_at=entry.created_at,
            )
        )

    for note in notes:
        items.append(
            TimelineEntry(
                id=f"note-{note.id}",
                type="note",
                message=note.message,
                user_name=note.user.full_name if note.user else None,
                created_at=note.created_at,
            )
        )

    items.sort(key=lambda x: x.created_at)
    return items


def to_incident_list_item(event: FireEvent) -> IncidentListItemOut:
    device = event.device
    site = device.site if device else None
    fire_id = event.id
    return IncidentListItemOut(
        id=fire_id,
        fire_event_id=fire_id,
        device_id=event.device_id,
        device_name=device.name if device else None,
        site_name=site.name if site else None,
        confidence=event.confidence,
        event_type=event.event_type,
        image_url=event.image_url,
        video_url=event.video_url,
        temperature=event.temperature,
        status=event.status,
        created_at=event.created_at,
    )


def to_incident_detail(
    event: FireEvent,
    device: Device | None,
    site: Site | None,
    notes: list[IncidentNote],
    timeline: list[TimelineEntry],
) -> IncidentDetailOut:
    device_name = device.name if device else None
    site_name = site.name if site else None
    fire_id = event.id
    note_outs = [
        IncidentNoteOut(
            id=n.id,
            incident_id=n.incident_id,
            user_id=n.user_id,
            user_name=n.user.full_name if n.user else None,
            message=n.message,
            created_at=n.created_at,
        )
        for n in notes
    ]
    return IncidentDetailOut(
        id=fire_id,
        fire_event_id=fire_id,
        device_id=event.device_id,
        device_name=device_name,
        site_name=site_name,
        device=(
            IncidentDeviceOut(
                id=device.id,
                device_uid=device.device_uid,
                name=device.name,
            )
            if device
            else None
        ),
        site=(IncidentSiteOut(id=site.id, name=site.name) if site else None),
        confidence=event.confidence,
        event_type=event.event_type,
        image_url=event.image_url,
        video_url=event.video_url,
        temperature=event.temperature,
        status=event.status,
        created_at=event.created_at,
        notes=note_outs,
        timeline=timeline,
    )


def load_incident_detail(
    db: Session,
    incident_id: int,
    current_user: User,
    *,
    audit_organization_id: int | None = None,
) -> IncidentDetailOut:
    organization_id = get_effective_organization_id(current_user)
    event, device, site = get_incident_context(db, incident_id, organization_id)
    fire_event_id = event.id

    notes = (
        db.query(IncidentNote)
        .options(joinedload(IncidentNote.user))
        .filter(IncidentNote.incident_id == fire_event_id)
        .order_by(IncidentNote.created_at.asc())
        .all()
    )

    audit_q = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .filter(
            AuditLog.entity_type == "incident",
            AuditLog.entity_id == fire_event_id,
        )
    )
    if audit_organization_id is not None:
        audit_q = audit_q.filter(AuditLog.organization_id == audit_organization_id)

    audit_entries = audit_q.order_by(AuditLog.created_at.asc()).all()
    timeline = build_timeline(event, notes, audit_entries)
    return to_incident_detail(event, device, site, notes, timeline)


def list_incidents_for_org(
    db: Session,
    organization_id: int | None,
    *,
    include_all: bool = False,
    open_status_values: list[str],
) -> list[IncidentListItemOut]:
    q = scoped_fire_events_query(db, organization_id)
    if not include_all:
        q = q.filter(FireEvent.status.in_(open_status_values))
    events = q.order_by(FireEvent.created_at.desc()).limit(200).all()

    list_ids = [e.id for e in events]
    logger.info(
        "incident_list organization_id=%s count=%s ids=%s",
        organization_id,
        len(list_ids),
        list_ids,
    )

    return [to_incident_list_item(event) for event in events]
