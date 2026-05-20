import argparse
import logging
import os
import time
from pathlib import Path

import requests

from env_loader import load_project_env
from event_queue import dequeue_all, enqueue, save_queue
from metrics import collect_metrics

load_project_env()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

DEVICE_UID = os.getenv("DEVICE_UID", "pi-001")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "SUPER_SECRET_KEY_123")
CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://localhost:8000").rstrip("/")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")

HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))
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
            response = requests.request(method, url, headers=API_HEADERS, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            logging.error("Attempt %s failed for %s: %s", attempt, url, error)
            if attempt < RETRY_MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"Request failed after {RETRY_MAX_ATTEMPTS} attempts") from last_error


def send_heartbeat() -> dict:
    metrics = collect_metrics()
    payload = {
        "device_uid": DEVICE_UID,
        "cpu_temp": metrics.get("cpu_temp"),
        "ram_usage": metrics.get("ram_usage"),
        "disk_usage": metrics.get("disk_usage"),
        "camera_status": metrics.get("camera_status"),
        "agent_version": AGENT_VERSION,
    }
    url = f"{CLOUD_API_URL}/api/device/heartbeat"
    logging.info("POST %s", url)
    response = _request_with_retries("POST", url, json=payload)
    return response.json()


def send_fire_event(
    confidence: float,
    temperature: float | None = None,
    image_url: str | None = None,
    video_url: str | None = None,
    *,
    queue_on_failure: bool = True,
):
    payload = {
        "device_uid": DEVICE_UID,
        "confidence": confidence,
        "event_type": "fire_detected",
        "image_url": image_url,
        "video_url": video_url,
        "temperature": temperature,
    }

    url = f"{CLOUD_API_URL}/api/device/events/fire"
    logging.info("Sending fire event to %s", url)

    try:
        response = _request_with_retries("POST", url, json=payload)
        logging.info("Fire event accepted: %s", response.text)
        return response.json()
    except RuntimeError as error:
        if queue_on_failure:
            enqueue(payload)
            logging.error("Fire event queued for retry: %s", error)
            return {"queued": True}
        raise


def flush_pending_events() -> int:
    pending = dequeue_all()
    if not pending:
        return 0

    sent = 0
    failed: list[dict] = []
    for payload in pending:
        try:
            url = f"{CLOUD_API_URL}/api/device/events/fire"
            _request_with_retries("POST", url, json=payload)
            sent += 1
            logging.info("Replayed queued fire event")
        except RuntimeError:
            failed.append(payload)

    if failed:
        save_queue(failed)
    return sent


def send_fire_event_with_media(
    confidence: float,
    temperature: float | None = None,
    image_path: str | Path | None = None,
    video_path: str | Path | None = None,
):
    from storage.r2_uploader import R2Uploader

    uploader = R2Uploader()
    image_url = uploader.upload_image(image_path) if image_path else None
    video_url = uploader.upload_video(video_path) if video_path else None

    return send_fire_event(
        confidence=confidence,
        temperature=temperature,
        image_url=image_url,
        video_url=video_url,
    )


def check_fire_detection() -> bool:
    """Plug in camera / ML detection here. Return True to send a fire event."""
    return False


def run_production_loop():
    logging.info(
        "Starting production agent uid=%s api=%s version=%s",
        DEVICE_UID,
        CLOUD_API_URL,
        AGENT_VERSION,
    )

    while True:
        try:
            result = send_heartbeat()
            logging.info("Heartbeat OK: %s", result.get("status"))
            replayed = flush_pending_events()
            if replayed:
                logging.info("Replayed %s queued fire event(s)", replayed)
        except RuntimeError as error:
            logging.error("Heartbeat failed: %s", error)

        if check_fire_detection():
            logging.warning("Fire detection triggered")
            send_fire_event(confidence=0.95, temperature=collect_metrics().get("cpu_temp"))

        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


def run_heartbeat_test() -> int:
    """Send one heartbeat (same logic as --run) and exit."""
    print("Sending heartbeat...")
    try:
        result = send_heartbeat()
        print("Heartbeat success")
        logging.info("Response: %s", result)
        return 0
    except RuntimeError as error:
        print("Heartbeat failed")
        logging.error("%s", error)
        return 1


def run_test(image_path: str | None = None, video_path: str | None = None):
    logging.info("Running NaarFind edge-agent test mode")

    if image_path or video_path:
        result = send_fire_event_with_media(
            confidence=0.96,
            temperature=54.2,
            image_path=image_path,
            video_path=video_path,
        )
    else:
        r2_configured = all(
            os.getenv(key)
            for key in (
                "R2_ACCOUNT_ID",
                "R2_ACCESS_KEY_ID",
                "R2_SECRET_ACCESS_KEY",
                "R2_BUCKET",
                "R2_PUBLIC_URL",
            )
        )
        if r2_configured:
            logging.warning(
                "R2 is configured but no --image/--video provided; sending test URLs only. "
                "Use: python agent.py --test --image path/to.jpg --video path/to.mp4"
            )

        result = send_fire_event(
            confidence=0.96,
            temperature=54.2,
            image_url=f"{os.getenv('R2_PUBLIC_URL', 'https://example.com').rstrip('/')}/test/fire-test.jpg",
            video_url=f"{os.getenv('R2_PUBLIC_URL', 'https://example.com').rstrip('/')}/test/fire-test.mp4",
            queue_on_failure=False,
        )

    logging.info("Test event sent successfully: %s", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="NaarFind Raspberry Pi Edge Agent")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test", action="store_true", help="Send one test fire event")
    mode.add_argument(
        "--heartbeat-test",
        action="store_true",
        help="Send one heartbeat to the backend and exit",
    )
    mode.add_argument("--run", action="store_true", help="Production loop: heartbeat + detection")
    mode.add_argument(
        "--r2-test",
        action="store_true",
        help="Upload sample image to R2 and print public URL",
    )
    parser.add_argument("--image", type=str, help="Local image file (use with --test)")
    parser.add_argument("--video", type=str, help="Local video file (use with --test)")

    args = parser.parse_args()

    if args.r2_test:
        from test_r2_upload import main as r2_test_main

        raise SystemExit(r2_test_main())
    if args.heartbeat_test:
        raise SystemExit(run_heartbeat_test())
    if args.test:
        run_test(image_path=args.image, video_path=args.video)
    elif args.run:
        run_production_loop()


if __name__ == "__main__":
    main()
