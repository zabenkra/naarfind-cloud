import argparse
import logging
import os
import time
from pathlib import Path

import requests

from env_loader import load_project_env

load_project_env()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

DEVICE_UID = os.getenv("DEVICE_UID", "pi-001")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "SUPER_SECRET_KEY_123")
CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://localhost:8000").rstrip("/")

RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BACKOFF_SECONDS = int(os.getenv("RETRY_BACKOFF_SECONDS", "2"))


def send_fire_event(
    confidence: float,
    temperature: float | None = None,
    image_url: str | None = None,
    video_url: str | None = None,
):
    url = f"{CLOUD_API_URL}/api/device/events/fire"

    payload = {
        "device_uid": DEVICE_UID,
        "confidence": confidence,
        "event_type": "fire_detected",
        "image_url": image_url,
        "video_url": video_url,
        "temperature": temperature,
    }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": DEVICE_API_KEY,
    }

    logging.info("Sending fire event to %s", url)
    logging.info("Payload: %s", payload)

    last_error = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            logging.info("Response status: %s", response.status_code)
            logging.info("Response body: %s", response.text)

            response.raise_for_status()
            return response.json()

        except requests.RequestException as error:
            last_error = error
            logging.error("Attempt %s failed: %s", attempt, error)

            if attempt < RETRY_MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise RuntimeError("Failed to send fire event after retries") from last_error


def send_fire_event_with_media(
    confidence: float,
    temperature: float | None = None,
    image_path: str | Path | None = None,
    video_path: str | Path | None = None,
):
    """Upload media to R2, then send fire event with public URLs."""
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
        )

    logging.info("Test event sent successfully: %s", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="NaarFind Raspberry Pi Edge Agent")
    parser.add_argument("--test", action="store_true", help="Send a fake fire event")
    parser.add_argument("--image", type=str, help="Local image file to upload to R2")
    parser.add_argument("--video", type=str, help="Local video file to upload to R2")
    parser.add_argument(
        "--r2-test",
        action="store_true",
        help="Upload sample image to R2 and print public URL",
    )

    args = parser.parse_args()

    if args.r2_test:
        from test_r2_upload import main as r2_test_main

        raise SystemExit(r2_test_main())
    if args.test:
        run_test(image_path=args.image, video_path=args.video)
    else:
        logging.info("No mode selected. Use: python agent.py --test or --r2-test")


if __name__ == "__main__":
    main()
