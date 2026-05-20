import argparse
import logging
import os
import threading
import time
from pathlib import Path

import requests

from env_loader import load_project_env
from api_client import flush_pending_events, send_fire_event_payload
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

_heartbeat_stop = threading.Event()
_detector_loop = None

# Bump when CLI changes — verify on Pi: python agent.py --version
CLI_VERSION = "2.1.0"


def _request_with_retries(method: str, url: str, **kwargs) -> requests.Response:
    from api_client import _request_with_retries as _api_request

    return _api_request(method, url, **kwargs)


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
    event_type: str = "fire_detected",
    queue_on_failure: bool = True,
):
    return send_fire_event_payload(
        {
            "confidence": confidence,
            "event_type": event_type,
            "image_url": image_url,
            "video_url": video_url,
            "temperature": temperature,
        },
        queue_on_failure=queue_on_failure,
    )


def send_fire_event_with_media(
    confidence: float,
    temperature: float | None = None,
    image_path: str | Path | None = None,
    video_path: str | Path | None = None,
    event_type: str = "fire_detected",
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
        event_type=event_type,
    )


def handle_detection_alert(alert: dict) -> None:
    """Publish confirmed detection to R2 + Railway (see events.py)."""
    from events import publish_detection_event

    result = publish_detection_event(alert)
    if not result.get("ok"):
        logging.error("Alert pipeline failed: %s", result.get("error"))


def _heartbeat_loop() -> None:
    while not _heartbeat_stop.is_set():
        try:
            result = send_heartbeat()
            logging.info("Heartbeat OK: %s", result.get("status"))
            replayed = flush_pending_events()
            if replayed:
                logging.info("Replayed %s queued fire event(s)", replayed)
        except RuntimeError as error:
            logging.error("Heartbeat failed: %s", error)
        _heartbeat_stop.wait(HEARTBEAT_INTERVAL_SECONDS)


def start_heartbeat_thread() -> threading.Thread:
    global _heartbeat_stop
    _heartbeat_stop = threading.Event()
    thread = threading.Thread(target=_heartbeat_loop, name="heartbeat", daemon=True)
    thread.start()
    logging.info("Heartbeat thread started (interval=%ss)", HEARTBEAT_INTERVAL_SECONDS)
    return thread


def stop_heartbeat_thread() -> None:
    _heartbeat_stop.set()


def start_detection(*, show_gui: bool = False) -> bool:
    """Start detector.fire_detector loop in a background thread."""
    global _detector_loop
    from detector.fire_detector import FireDetectorLoop

    _detector_loop = FireDetectorLoop(
        on_alert=handle_detection_alert,
        debug_window=show_gui,
    )
    if not _detector_loop.start():
        logging.warning(
            "Detection disabled — model not found. "
            "Place NCNN or .pt model in models/ (see models/README.md)"
        )
        return False
    logging.info("Detection started (gui=%s)", show_gui)
    return True


def stop_detection() -> None:
    global _detector_loop
    if _detector_loop:
        _detector_loop.stop()
        _detector_loop = None


def _wait_until_interrupt() -> None:
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")


def run_production_loop() -> None:
    """--run: heartbeat + detection (heartbeat only if model missing)."""
    logging.info(
        "Starting production agent uid=%s api=%s version=%s",
        DEVICE_UID,
        CLOUD_API_URL,
        AGENT_VERSION,
    )

    start_heartbeat_thread()
    if not start_detection(show_gui=False):
        logging.warning("Running heartbeat only — no detection model")

    try:
        _wait_until_interrupt()
    finally:
        stop_detection()
        stop_heartbeat_thread()


def run_detect_mode(*, debug: bool) -> int:
    """
    --detect / --detect-debug: detection loop + heartbeat.
    GUI preview only when debug=True AND ENABLE_DEBUG_WINDOW=true.
    """
    from detector.config import config

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Debug logging enabled")

    show_gui = debug and config.enable_debug_window
    if debug and not config.enable_debug_window:
        logging.info(
            "GUI preview disabled (set ENABLE_DEBUG_WINDOW=true to enable OpenCV window)"
        )

    start_heartbeat_thread()

    if not start_detection(show_gui=show_gui):
        print(
            "WARNING: Model not loaded — heartbeat running, detection disabled.\n"
            f"  MODEL_PATH={config.model_path}\n"
            f"  MODEL_FALLBACK_PATH={config.model_fallback_path}"
        )
        print("Press Ctrl+C to stop heartbeat.")
        try:
            _wait_until_interrupt()
        finally:
            stop_heartbeat_thread()
        return 0

    print("Detection running. Ctrl+C to stop.")
    try:
        _wait_until_interrupt()
    finally:
        stop_detection()
        stop_heartbeat_thread()
    return 0


def run_heartbeat_test() -> int:
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
        result = send_fire_event(
            confidence=0.96,
            temperature=54.2,
            image_url=f"{os.getenv('R2_PUBLIC_URL', 'https://example.com').rstrip('/')}/test/fire-test.jpg",
            video_url=f"{os.getenv('R2_PUBLIC_URL', 'https://example.com').rstrip('/')}/test/fire-test.mp4",
            queue_on_failure=False,
        )

    logging.info("Test event sent successfully: %s", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NaarFind Raspberry Pi Edge Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes (pick exactly one):\n"
            "  --camera-test     Capture one frame → snapshots/camera_test.jpg\n"
            "  --detect          Fire/smoke detection + heartbeat (no GUI)\n"
            "  --detect-debug    Detection + verbose logs; GUI if ENABLE_DEBUG_WINDOW=true\n"
            "  --run             Production: heartbeat + detection\n"
            "  --heartbeat-test  Send one heartbeat\n"
            "  --test            Send one test fire event\n"
            "  --r2-test         Test Cloudflare R2 upload\n"
            "\n"
            "If you only see --test --heartbeat-test --run --r2-test, run: git pull\n"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"NaarFind edge-agent {CLI_VERSION}",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test", action="store_true", help="Send one test fire event")
    mode.add_argument("--heartbeat-test", action="store_true", help="Send one heartbeat")
    mode.add_argument(
        "--camera-test",
        action="store_true",
        help="CSI/OpenCV camera → snapshots/camera_test.jpg",
    )
    mode.add_argument(
        "--detect",
        action="store_true",
        help="Detection loop + heartbeat (no GUI)",
    )
    mode.add_argument(
        "--detect-debug",
        action="store_true",
        help="Detection + debug logs; GUI only if ENABLE_DEBUG_WINDOW=true",
    )
    mode.add_argument(
        "--run",
        action="store_true",
        help="Production: heartbeat + detection (heartbeat only if no model)",
    )
    mode.add_argument("--r2-test", action="store_true", help="Upload sample image to R2")
    # Optional extras (backward compatible)
    mode.add_argument("--ai-test", action="store_true", help="Load model, one inference")
    mode.add_argument("--run-ai", action="store_true", help="Alias for --run with AI pipeline")
    parser.add_argument("--image", type=str, help="Local image (with --test)")
    parser.add_argument("--video", type=str, help="Local video (with --test)")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.r2_test:
        from test_r2_upload import main as r2_test_main

        raise SystemExit(r2_test_main())
    if args.heartbeat_test:
        raise SystemExit(run_heartbeat_test())
    if args.camera_test:
        from detector.camera import run_camera_test

        raise SystemExit(run_camera_test())
    if args.ai_test:
        try:
            from ai.detector import run_ai_test

            raise SystemExit(run_ai_test())
        except ImportError:
            logging.error("ai module not available; use --detect after placing model in models/")
            raise SystemExit(1) from None
    if args.test:
        run_test(image_path=args.image, video_path=args.video)
        return
    if args.detect_debug:
        raise SystemExit(run_detect_mode(debug=True))
    if args.detect:
        raise SystemExit(run_detect_mode(debug=False))
    if args.run or args.run_ai:
        run_production_loop()
        return

    parser.error("No mode selected")


if __name__ == "__main__":
    main()
