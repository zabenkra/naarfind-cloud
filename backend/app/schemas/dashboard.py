from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    total_devices: int = Field(..., ge=0)
    online_devices: int = Field(..., ge=0)
    fire_events: int = Field(..., ge=0)
    open_incidents: int = Field(..., ge=0)
