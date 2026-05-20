from app.models.models import Device
from app.schemas.devices import DeviceOut
from app.services.device_status import connection_status, is_device_online


def device_to_out(device: Device, site_name: str | None = None) -> DeviceOut:
    status = connection_status(device.last_seen)
    return DeviceOut(
        id=device.id,
        site_id=device.site_id,
        site_name=site_name,
        name=device.name,
        device_uid=device.device_uid,
        status=status,
        is_online=is_device_online(device.last_seen),
        last_seen=device.last_seen,
        cpu_temp=device.cpu_temp,
        ram_usage=device.ram_usage,
        disk_usage=device.disk_usage,
        camera_status=device.camera_status,
        agent_version=device.agent_version,
        created_at=device.created_at,
    )
