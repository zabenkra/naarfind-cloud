import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id, require_roles
from app.models.models import UserRole
from app.models.models import AuditLog, IncidentNote, User
from app.schemas.fire_event_status import OPEN_INCIDENT_STATUSES
from app.schemas.incidents import (
    IncidentDetailOut,
    IncidentListItemOut,
    IncidentNoteCreate,
    IncidentNoteOut,
    IncidentStatusUpdate,
)
from app.services.audit import record_audit
from app.services.incidents import (
    get_incident_context,
    list_incidents_for_org,
    load_incident_detail,
)

logger = logging.getLogger(__name__)

# Prefix is applied in app/main.py: include_router(..., prefix="/api/incidents")
router = APIRouter(tags=["incidents"])

OPEN_STATUS_VALUES = [s.value for s in OPEN_INCIDENT_STATUSES]


def _audit_org_id(user: User) -> int | None:
    if user.role == "super_admin":
        return None
    return user.organization_id


# --- Static paths first (before /{incident_id}) ---


@router.get("/debug/routes")
def incidents_debug_routes():
    """Temporary: confirm incident routes are mounted in production."""
    return {"routes": ["list", "detail", "status", "notes", "debug"]}


@router.get("", response_model=list[IncidentListItemOut])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_all: bool = Query(False, description="Include resolved and false_alarm"),
):
    org_id = get_effective_organization_id(current_user)
    return list_incidents_for_org(
        db,
        org_id,
        include_all=include_all,
        open_status_values=OPEN_STATUS_VALUES,
    )


# --- More specific dynamic paths before bare /{incident_id} ---


@router.get("/{incident_id}/notes", response_model=list[IncidentNoteOut])
def list_incident_notes(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)
    event, _, _ = get_incident_context(db, incident_id, org_id)
    fire_event_id = event.id

    notes = (
        db.query(IncidentNote)
        .options(joinedload(IncidentNote.user))
        .filter(IncidentNote.incident_id == fire_event_id)
        .order_by(IncidentNote.created_at.asc())
        .all()
    )

    return [
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


@router.post("/{incident_id}/notes", response_model=IncidentNoteOut, status_code=201)
def add_incident_note(
    incident_id: int,
    payload: IncidentNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.OPERATOR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    org_id = get_effective_organization_id(current_user)
    event, _, _ = get_incident_context(db, incident_id, org_id)
    fire_event_id = event.id

    note = IncidentNote(
        incident_id=fire_event_id,
        user_id=current_user.id,
        message=payload.message.strip(),
    )
    db.add(note)
    db.flush()

    record_audit(
        db,
        user=current_user,
        action="note_added",
        entity_type="incident",
        entity_id=fire_event_id,
        metadata={"note_id": note.id},
    )
    db.commit()
    db.refresh(note)

    user = db.query(User).filter(User.id == current_user.id).first()
    return IncidentNoteOut(
        id=note.id,
        incident_id=note.incident_id,
        user_id=note.user_id,
        user_name=user.full_name if user else current_user.full_name,
        message=note.message,
        created_at=note.created_at,
    )


@router.patch("/{incident_id}/status", response_model=IncidentDetailOut)
def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.OPERATOR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    org_id = get_effective_organization_id(current_user)
    event, _, _ = get_incident_context(db, incident_id, org_id)
    fire_event_id = event.id

    old_status = event.status
    new_status = payload.status.value
    if old_status == new_status:
        raise HTTPException(status_code=400, detail="Status is already set to this value")

    event.status = new_status
    record_audit(
        db,
        user=current_user,
        action="status_changed",
        entity_type="incident",
        entity_id=fire_event_id,
        metadata={"old_status": old_status, "new_status": new_status},
    )
    db.commit()

    return load_incident_detail(
        db,
        fire_event_id,
        current_user,
        audit_organization_id=_audit_org_id(current_user),
    )


# --- Detail last: must not shadow /notes, /status, /debug/routes ---


@router.get("/{incident_id}", response_model=IncidentDetailOut)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Incident detail by fire_events.id (same id as GET /api/incidents list)."""
    logger.info(
        "INCIDENT DETAIL HIT id=%s user=%s org=%s",
        incident_id,
        current_user.id,
        current_user.organization_id,
    )
    return load_incident_detail(
        db,
        incident_id,
        current_user,
        audit_organization_id=_audit_org_id(current_user),
    )
