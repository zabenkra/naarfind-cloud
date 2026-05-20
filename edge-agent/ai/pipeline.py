"""Production AI loop: camera → inference → temporal filter → cloud alerts."""

import logging
import threading
import time
from typing import Callable

from detector.config import config
from detector.fire_detector import FireDetectorLoop

logger = logging.getLogger(__name__)


class AIPipeline:
    """
    Fire/smoke detection pipeline with FPS, inference, and cooldown logging.
    Runs in a background thread (does not block heartbeat).
    """

    def __init__(
        self,
        on_alert: Callable[[dict], None],
        debug_window: bool = False,
    ) -> None:
        self._on_alert = on_alert
        self._debug_window = debug_window
        self._loop: FireDetectorLoop | None = None
        self._status_thread: threading.Thread | None = None
        self._stop_status = threading.Event()
        self._last_log_time = 0.0
        self._last_inference_ms = 0.0
        self._last_detections: list = []
        self._processed_fps = 0.0
        self._capture_fps = 0.0

    def _wrapped_alert(self, alert: dict) -> None:
        cooldown_left = 0.0
        if self._loop and self._loop._last_alert_time > 0:
            elapsed = time.time() - self._loop._last_alert_time
            cooldown_left = max(0, config.detection_cooldown - elapsed)

        logger.warning(
            "ALERT | type=%s fire=%.2f smoke=%.2f risk=%s | cooldown_reset=%ss",
            alert.get("event_type"),
            alert.get("fire_confidence", 0),
            alert.get("smoke_confidence", 0),
            alert.get("risk_level"),
            config.detection_cooldown,
        )
        self._on_alert(alert)

    def _status_loop(self) -> None:
        while not self._stop_status.is_set():
            if self._loop:
                in_cooldown = self._loop._in_cooldown()
                cooldown_left = 0.0
                if in_cooldown and self._loop._last_alert_time > 0:
                    cooldown_left = max(
                        0,
                        config.detection_cooldown - (time.time() - self._loop._last_alert_time),
                    )

                logger.info(
                    "AI status | capture_fps=%.1f processed_fps=%.1f infer_ms=%.0f "
                    "detections=%d cooldown=%s (%.0fs left)",
                    self._capture_fps,
                    self._processed_fps,
                    self._last_inference_ms,
                    len(self._last_detections),
                    "active" if in_cooldown else "ready",
                    cooldown_left,
                )
            self._stop_status.wait(5.0)

    def start(self) -> bool:
        self._loop = FireDetectorLoop(
            on_alert=self._wrapped_alert,
            debug_window=self._debug_window,
        )
        ok = self._loop.start()
        if ok:
            self._stop_status.clear()
            self._status_thread = threading.Thread(
                target=self._status_loop,
                name="ai-status-log",
                daemon=True,
            )
            self._status_thread.start()
            logger.info(
                "AI pipeline started | process_every_n=%s cooldown=%ss",
                config.process_every_n_frames,
                config.detection_cooldown,
            )
        return ok

    def stop(self) -> None:
        self._stop_status.set()
        if self._status_thread and self._status_thread.is_alive():
            self._status_thread.join(timeout=2.0)
        if self._loop:
            self._loop.stop()
            self._loop = None
        logger.info("AI pipeline stopped")

    def log_frame_stats(
        self,
        *,
        inference_ms: float,
        detections: list,
        capture_fps: float | None,
        processed_fps: float | None,
    ) -> None:
        """Optional hook for per-frame stats (called from detector if extended)."""
        self._last_inference_ms = inference_ms
        self._last_detections = detections
        if capture_fps is not None:
            self._capture_fps = capture_fps
        if processed_fps is not None:
            self._processed_fps = processed_fps
