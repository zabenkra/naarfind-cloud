import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AgentConfig:
    device_uid: str
    device_api_key: str
    cloud_api_url: str
    retry_max_attempts: int
    retry_backoff_seconds: float

    @property
    def fire_event_url(self) -> str:
        base = self.cloud_api_url.rstrip("/")
        return f"{base}/api/device/events/fire"


def load_config() -> AgentConfig:
    device_uid = os.getenv("DEVICE_UID", "").strip()
    device_api_key = os.getenv("DEVICE_API_KEY", "").strip()
    cloud_api_url = os.getenv("CLOUD_API_URL", "").strip()

    if not device_uid:
        raise ValueError("DEVICE_UID is required in .env")
    if not device_api_key:
        raise ValueError("DEVICE_API_KEY is required in .env")
    if not cloud_api_url:
        raise ValueError("CLOUD_API_URL is required in .env")

    return AgentConfig(
        device_uid=device_uid,
        device_api_key=device_api_key,
        cloud_api_url=cloud_api_url,
        retry_max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
        retry_backoff_seconds=float(os.getenv("RETRY_BACKOFF_SECONDS", "2")),
    )
