"""Snapshot and visualization helpers."""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def draw_boxes(frame_rgb: np.ndarray, detections: list[dict]) -> np.ndarray:
    """Draw bounding boxes on RGB frame (returns BGR for cv2.imwrite)."""
    import cv2

    img = cv2.cvtColor(frame_rgb.copy(), cv2.COLOR_RGB2BGR)
    colors = {"fire": (0, 0, 255), "smoke": (128, 128, 128)}

    for det in detections:
        label = det.get("label", "?")
        conf = det.get("confidence", 0)
        x1, y1, x2, y2 = det.get("bbox", [0, 0, 0, 0])
        color = colors.get(label, (0, 255, 255))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            img,
            f"{label} {conf:.2f}",
            (x1, max(y1 - 8, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )
    return img


def save_snapshot(
    frame_rgb: np.ndarray,
    detections: list[dict],
    snapshot_dir: Path,
    prefix: str = "alert",
) -> Path:
    import cv2

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    path = snapshot_dir / f"{prefix}_{timestamp}.jpg"
    annotated = draw_boxes(frame_rgb, detections)
    cv2.imwrite(str(path), annotated)
    logger.info("snapshot saved path=%s", path)
    return path


def log_performance(
    *,
    frame_index: int,
    processed_count: int,
    inference_ms: float,
    capture_fps: float | None = None,
    processed_fps: float | None = None,
) -> None:
    parts = [
        f"frame={frame_index}",
        f"processed={processed_count}",
        f"infer={inference_ms:.0f}ms",
    ]
    if capture_fps is not None:
        parts.append(f"capture_fps={capture_fps:.1f}")
    if processed_fps is not None:
        parts.append(f"processed_fps={processed_fps:.1f}")
    logger.info("Perf | %s", " | ".join(parts))


class FpsCounter:
    def __init__(self, window: float = 2.0) -> None:
        self.window = window
        self._times: list[float] = []

    def tick(self) -> float | None:
        now = time.perf_counter()
        self._times.append(now)
        cutoff = now - self.window
        self._times = [t for t in self._times if t >= cutoff]
        if len(self._times) < 2:
            return None
        return (len(self._times) - 1) / (self._times[-1] - self._times[0])
