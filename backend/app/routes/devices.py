from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_effective_organization_id
from app.models.models import Device, Site, User
from app.schemas.devices import DeviceOut
from app.services.device_serializer import device_to_out
from app.services.tenant import devices_query

router = APIRouter(prefix="/api/devices", tags=["Devices"])


def _list_devices_for_org(db: Session, org_id: int | None) -> list[DeviceOut]:
    if org_id is not None:
        rows = (
            devices_query(db, org_id)
            .with_entities(Device, Site.name)
            .order_by(Device.name.asc())
            .all()
        )
    else:
        rows = (
            db.query(Device, Site.name)
            .outerjoin(Site, Device.site_id == Site.id)
            .order_by(Device.name.asc())
            .all()
        )

    return [device_to_out(device, site_name) for device, site_name in rows]


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = get_effective_organization_id(current_user)
    return _list_devices_for_org(db, org_id)
