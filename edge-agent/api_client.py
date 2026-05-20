"""HTTP client for NaarFind cloud API (heartbeat + fire events)."""

import logging
import os
import time

import requests

from env_loader import load_project_env
from event_queue import dequeue_all, enqueue, save_queue

load_project_env()

logger = logging.getLogger(__name__)

DEVICE_UID = os.getenv("DEVICE_UID", "pi-001").strip()
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "SUPER_SECRET_KEY_123")
CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://localhost:8000").rstrip("/")

RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BACKOFF_SECONDS = int(os.getenv("RETRY_BACKOFF_SECONDS", "2"))

API_HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": DEVICE_API_KEY,
}


def _request_with_retries(method: str, url: str, **kwargs) -> requests.Response:
    last_error = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            response = requests.request(
                method, url, headers=API_HEADERS, timeout=30, **kwargs
            )
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            logger.error("Attempt %s failed for %s: %s", attempt, url, error)
            if attempt < RETRY_MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"Request failed after {RETRY_MAX_ATTEMPTS} attempts") from last_error


def send_fire_event_payload(payload: dict, *, queue_on_failure: bool = True) -> dict:
    api_payload = {
        "device_uid": payload.get("device_uid", DEVICE_UID),
        "confidence": float(payload.get("confidence", 0.0)),
        "event_type": payload.get("event_type", "fire_detected"),
        "image_url": payload.get("image_url"),
        "video_url": payload.get("video_url"),
        "temperature": payload.get("temperature"),
    }

    url = f"{CLOUD_API_URL}/api/device/events/fire"
    logger.info(
        "POST %s type=%s confidence=%.2f image=%s",
        url,
        api_payload["event_type"],
        api_payload["confidence"],
        "yes" if api_payload.get("image_url") else "no",
    )

    try:
        response = _request_with_retries("POST", url, json=api_payload)
        body = response.json()
        logger.info("fire event response: %s", body)
        logger.info("event sent successfully")
        return body
    except RuntimeError as error:
        if queue_on_failure:
            enqueue(api_payload)
            logger.error("API failed — event queued for retry: %s", error)
            return {"queued": True}
        logger.error("API failed: %s", error)
        raise


def flush_pending_events() -> int:
    pending = dequeue_all()
    if not pending:
        return 0

    sent = 0
    failed: list[dict] = []
    url = f"{CLOUD_API_URL}/api/device/events/fire"
    for payload in pending:
        try:
            _request_with_retries("POST", url, json=payload)
            sent += 1
            logger.info("Replayed queued fire event")
        except RuntimeError:
            failed.append(payload)

    if failed:
        save_queue(failed)
    return sent
