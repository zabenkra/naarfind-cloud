from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id, is_super_admin
from app.models.models import Device, FireEvent, Site, User
from app.schemas.dashboard import DashboardStats
from app.schemas.fire_event_status import OPEN_INCIDENT_STATUSES
from app.services.device_status import is_device_online
from app.services.tenant import devices_query, fire_events_query

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

OPEN_STATUS_VALUES = [s.value for s in OPEN_INCIDENT_STATUSES]


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)

    if org_id is not None:
        device_q = devices_query(db, org_id)
        event_q = fire_events_query(db, org_id)
        total_devices = device_q.count()
        online_devices = sum(
            1 for device in device_q.all() if is_device_online(device.last_seen)
        )
        fire_events = event_q.count()
        open_incidents = event_q.filter(FireEvent.status.in_(OPEN_STATUS_VALUES)).count()
    else:
        all_devices = db.query(Device).all()
        total_devices = len(all_devices)
        online_devices = sum(1 for d in all_devices if is_device_online(d.last_seen))
        fire_events = db.query(FireEvent).count()
        open_incidents = (
            db.query(FireEvent)
            .filter(FireEvent.status.in_(OPEN_STATUS_VALUES))
            .count()
        )

    return DashboardStats(
        total_devices=total_devices,
        online_devices=online_devices,
        fire_events=fire_events,
        open_incidents=open_incidents,
    )
