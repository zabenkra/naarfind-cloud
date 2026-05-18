from fastapi import APIRouter, Depends, HTTPException  # noqa: F401
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id, require_roles
from app.models.models import UserRole
from app.models.models import FireEvent, User
from app.schemas.fire_events import FireEventOut, FireEventStatusResponse, FireEventStatusUpdate
from app.services.fire_events import to_fire_event_out
from app.services.tenant import fire_events_query, get_fire_event_for_org

router = APIRouter(prefix="/api/events/fire", tags=["Fire Events"])


@router.get("", response_model=list[FireEventOut])
def list_fire_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)

    if org_id is not None:
        rows = (
            fire_events_query(db, org_id)
            .order_by(FireEvent.created_at.desc())
            .all()
        )
    else:
        from app.models.models import Device

        rows = (
            db.query(FireEvent, Device.name.label("device_name"))
            .outerjoin(Device, FireEvent.device_id == Device.id)
            .order_by(FireEvent.created_at.desc())
            .all()
        )

    return [to_fire_event_out(event, device_name) for event, device_name in rows]


@router.patch("/{event_id}/status", response_model=FireEventStatusResponse)
def update_fire_event_status(
    event_id: int,
    payload: FireEventStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.OPERATOR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN)),
):
    org_id = get_effective_organization_id(current_user)

    if org_id is not None:
        event = get_fire_event_for_org(db, event_id, org_id)
    else:
        event = db.query(FireEvent).filter(FireEvent.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Fire event not found")

    event.status = payload.status.value
    db.commit()
    db.refresh(event)

    return FireEventStatusResponse(id=event.id, status=payload.status)
