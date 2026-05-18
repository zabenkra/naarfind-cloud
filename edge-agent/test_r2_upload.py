#!/usr/bin/env python3
"""Upload a sample image to Cloudflare R2 and print the public URL."""

import logging
import struct
import sys
import zlib
from pathlib import Path

from env_loader import EDGE_AGENT_DIR, load_project_env, r2_configured
from storage.r2_uploader import R2Uploader

SAMPLE_IMAGE = EDGE_AGENT_DIR / "samples" / "test-fire.png"


def create_sample_image(dest: Path) -> Path:
    """Create a small orange PNG (stdlib only) for upload testing."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    width, height = 64, 64
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend((255, 120, 40, 255))  # orange RGBA

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0),
    )
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")

    dest.write_bytes(png)
    return dest


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    load_project_env()

    if not r2_configured():
        logging.error(
            "R2 is not configured. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
            "R2_SECRET_ACCESS_KEY, R2_BUCKET, and R2_PUBLIC_URL in "
            "the project root .env or edge-agent/.env"
        )
        return 1

    sample = SAMPLE_IMAGE if SAMPLE_IMAGE.is_file() else create_sample_image(SAMPLE_IMAGE)
    logging.info("Using sample image: %s (%s bytes)", sample, sample.stat().st_size)

    try:
        uploader = R2Uploader()
        public_url = uploader.upload_image(sample)
    except Exception as exc:
        logging.error("Upload failed: %s", exc)
        if "SignatureDoesNotMatch" in str(exc):
            logging.error(
                "Check R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY in .env — "
                "regenerate the token in Cloudflare R2 → Manage R2 API Tokens."
            )
        return 1

    print("\n=== R2 upload successful ===")
    print(f"Public URL: {public_url}")
    print("============================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
