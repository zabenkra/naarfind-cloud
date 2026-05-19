"""Persist fire events when the cloud API is unreachable."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

QUEUE_PATH = Path(__file__).resolve().parent / "data" / "pending_fire_events.json"


def _ensure_parent() -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_queue() -> list[dict]:
    if not QUEUE_PATH.is_file():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as error:
        logger.warning("Could not read event queue: %s", error)
        return []


def save_queue(events: list[dict]) -> None:
    _ensure_parent()
    QUEUE_PATH.write_text(json.dumps(events, indent=2), encoding="utf-8")


def enqueue(event: dict) -> None:
    events = load_queue()
    events.append(event)
    save_queue(events)
    logger.warning("Queued fire event (offline). Queue size: %s", len(events))


def dequeue_all() -> list[dict]:
    events = load_queue()
    if events:
        save_queue([])
    return events
