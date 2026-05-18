"""Cloudflare R2 uploads via S3-compatible API (boto3)."""

import logging
import mimetypes
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from env_loader import load_project_env

load_project_env()

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


class R2Uploader:
    def __init__(self):
        def _env(name: str) -> str:
            return os.getenv(name, "").strip().strip('"').strip("'")

        self.account_id = _env("R2_ACCOUNT_ID")
        self.access_key_id = _env("R2_ACCESS_KEY_ID")
        self.secret_access_key = _env("R2_SECRET_ACCESS_KEY")
        self.bucket = _env("R2_BUCKET")
        self.public_url = _env("R2_PUBLIC_URL").rstrip("/")
        self.device_uid = os.getenv("DEVICE_UID", "pi-001").strip()
        self.retry_max_attempts = int(os.getenv("R2_RETRY_MAX_ATTEMPTS", "3"))
        self.retry_backoff_seconds = float(os.getenv("R2_RETRY_BACKOFF_SECONDS", "2"))

        self._client = None
        self._validate_config()

    def _validate_config(self) -> None:
        missing = [
            name
            for name, value in [
                ("R2_ACCOUNT_ID", self.account_id),
                ("R2_ACCESS_KEY_ID", self.access_key_id),
                ("R2_SECRET_ACCESS_KEY", self.secret_access_key),
                ("R2_BUCKET", self.bucket),
                ("R2_PUBLIC_URL", self.public_url),
            ]
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required R2 environment variables: {', '.join(missing)}. "
                "Set them in the project root .env or edge-agent/.env"
            )

    @property
    def client(self):
        if self._client is None:
            endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
            logger.info("Connecting to R2 endpoint=%s bucket=%s", endpoint, self.bucket)
            self._client = boto3.client(
                service_name="s3",
                endpoint_url=endpoint,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    retries={"max_attempts": 0},
                ),
            )
        return self._client

    def _date_prefix(self, media_type: str) -> str:
        now = datetime.now(timezone.utc)
        return f"{media_type}/{now:%Y/%m/%d}"

    def _object_key(self, file_path: Path, media_type: str) -> str:
        suffix = file_path.suffix.lower() or ".bin"
        timestamp = datetime.now(timezone.utc).strftime("%H%M%S_%f")
        filename = f"{self.device_uid}_{timestamp}{suffix}"
        return f"{self._date_prefix(media_type)}/{filename}"

    def _guess_content_type(self, file_path: Path) -> str:
        content_type, _ = mimetypes.guess_type(str(file_path))
        return content_type or "application/octet-stream"

    def _public_url_for_key(self, key: str) -> str:
        return f"{self.public_url}/{key}"

    def _upload_file(self, file_path: str | Path, media_type: str) -> str:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        key = self._object_key(path, media_type)
        content_type = self._guess_content_type(path)
        last_error: Exception | None = None

        for attempt in range(1, self.retry_max_attempts + 1):
            logger.info(
                "R2 upload attempt %d/%d type=%s file=%s key=%s",
                attempt,
                self.retry_max_attempts,
                media_type,
                path.name,
                key,
            )
            try:
                with path.open("rb") as body:
                    self.client.put_object(
                        Bucket=self.bucket,
                        Key=key,
                        Body=body,
                        ContentType=content_type,
                    )
                public_url = self._public_url_for_key(key)
                logger.info("R2 upload success url=%s", public_url)
                return public_url
            except (ClientError, BotoCoreError, OSError) as exc:
                last_error = exc
                logger.warning("R2 upload attempt %d failed: %s", attempt, exc)
                if attempt < self.retry_max_attempts:
                    sleep_time = self.retry_backoff_seconds * attempt
                    logger.info("Retrying R2 upload in %.1fs...", sleep_time)
                    time.sleep(sleep_time)

        logger.error("R2 upload failed after %d attempts", self.retry_max_attempts)
        raise RuntimeError(f"R2 upload failed: {last_error}") from last_error

    def upload_image(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image type '{path.suffix}'. "
                f"Allowed: {', '.join(sorted(IMAGE_EXTENSIONS))}"
            )
        return self._upload_file(path, "images")

    def upload_video(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError(
                f"Unsupported video type '{path.suffix}'. "
                f"Allowed: {', '.join(sorted(VIDEO_EXTENSIONS))}"
            )
        return self._upload_file(path, "videos")
