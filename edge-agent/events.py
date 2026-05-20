"""
Production fire-event pipeline: snapshot → R2 → Railway API.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from metrics import collect_metrics

logger = logging.getLogger(__name__)

DEVICE_UID = os.getenv("DEVICE_UID", "pi-001").strip()


def _upload_snapshots_enabled() -> bool:
    return os.getenv("UPLOAD_SNAPSHOTS", "true").strip().lower() in ("1", "true", "yes")


def upload_snapshot(local_path: Path | None) -> str | None:
    if not local_path or not local_path.is_file():
        logger.info("snapshot upload skipped (no local file)")
        return None
    if not _upload_snapshots_enabled():
        logger.info("snapshot upload skipped (UPLOAD_SNAPSHOTS=false)")
        return None

    logger.info("snapshot upload started path=%s", local_path)
    try:
        from storage.r2_uploader import R2Uploader

        url = R2Uploader().upload_image(local_path)
        logger.warning("snapshot uploaded url=%s", url)
        return url
    except Exception as exc:
        logger.error("upload failed: %s", exc)
        return None


def build_event_payload(alert: dict) -> dict:
    """Full event document (logged locally; API gets safe subset)."""
    metrics = collect_metrics()
    return {
        "device_uid": DEVICE_UID,
        "event_type": alert.get("event_type", "fire"),
        "risk_level": alert.get("risk_level", "medium"),
        "fire_confidence": float(alert.get("fire_confidence", 0.0)),
        "smoke_confidence": float(alert.get("smoke_confidence", 0.0)),
        "confidence": float(alert.get("confidence", 0.0)),
        "temperature": metrics.get("cpu_temp"),
        "image_url": alert.get("image_url"),
        "local_image_path": alert.get("local_image_path") or (
            str(alert["local_path"]) if alert.get("local_path") else None
        ),
        "timestamp": alert.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }


def to_api_payload(event: dict) -> dict:
    """Fields accepted by POST /api/device/events/fire."""
    return {
        "device_uid": event["device_uid"],
        "confidence": event["confidence"],
        "event_type": event["event_type"],
        "image_url": event.get("image_url"),
        "video_url": None,
        "temperature": event.get("temperature"),
    }


def publish_detection_event(alert: dict) -> dict:
    """
    After temporal confirmation: upload snapshot (optional) and POST fire event.
    """
    from api_client import send_fire_event_payload

    local_path = alert.get("local_path")
    if local_path and not alert.get("local_image_path"):
        alert["local_image_path"] = str(local_path)

    if local_path:
        logger.info("snapshot saved path=%s", local_path)
    else:
        logger.warning("snapshot saved: no (SAVE_SNAPSHOTS=false or save error)")

    image_url = upload_snapshot(Path(local_path) if local_path else None)
    alert["image_url"] = image_url

    event = build_event_payload(alert)
    api_payload = to_api_payload(event)

    logger.info("fire event payload: %s", json.dumps(event, default=str))
    logger.info("API payload: %s", json.dumps(api_payload, default=str))

    try:
        response = send_fire_event_payload(api_payload, queue_on_failure=True)
        logger.info("fire event response: %s", response)
        if response.get("queued"):
            logger.warning("event queued for retry (API temporarily unavailable)")
            return {"ok": True, "queued": True, "event": event, "response": response}
        logger.warning("event sent successfully event_id=%s", response.get("event_id"))
        return {"ok": True, "event": event, "response": response}
    except Exception as exc:
        logger.error("API failed: %s", exc)
        return {"ok": False, "error": str(exc), "event": event}
