"""Main detection loop: camera capture, inference, temporal filter, alerts."""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from detector.camera import create_camera
from detector.config import DetectorConfig, config
from detector.inference import YOLOFireSmokeInference
from detector.temporal_filter import TemporalFilter, TemporalRule
from detector.utils import FpsCounter, log_performance, save_snapshot

logger = logging.getLogger(__name__)


def _risk_level(fire_conf: float, smoke_conf: float, event_type: str) -> str:
    peak = max(fire_conf, smoke_conf)
    if event_type == "fire_smoke" and peak >= 0.8:
        return "high"
    if peak >= 0.75:
        return "high"
    if peak >= 0.6:
        return "medium"
    return "low"


class FireDetectorLoop:
    """
    Continuous fire/smoke detection. Runs in a thread; does not block heartbeat.
    """

    def __init__(
        self,
        on_alert: Callable[[dict], None],
        cfg: DetectorConfig | None = None,
        debug_window: bool = False,
    ) -> None:
        self.cfg = cfg or config
        self.on_alert = on_alert
        # GUI only when caller explicitly enables it (e.g. --detect-debug + ENABLE_DEBUG_WINDOW)
        self.debug_window = debug_window
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_alert_time = 0.0
        self._inference: YOLOFireSmokeInference | None = None

    def start(self) -> bool:
        """Start detection thread. Returns False if model missing (heartbeat can continue)."""
        self._inference = YOLOFireSmokeInference()
        if not self._inference.load_model():
            logger.warning("Detection disabled — model not available")
            return False

        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="fire-detector",
            daemon=True,
        )
        self._thread.start()
        logger.info("Fire detector thread started")
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._thread = None

    def _in_cooldown(self) -> bool:
        if self._last_alert_time <= 0:
            return False
        return (time.time() - self._last_alert_time) < self.cfg.detection_cooldown

    def _run_loop(self) -> None:
        camera = None
        temporal = TemporalFilter(
            fire_rule=TemporalRule(self.cfg.fire_required, self.cfg.fire_window),
            smoke_rule=TemporalRule(self.cfg.smoke_required, self.cfg.smoke_window),
            both_rule=TemporalRule(self.cfg.both_required, self.cfg.both_window),
        )
        frame_index = 0
        processed_count = 0
        capture_fps_counter = FpsCounter()
        process_fps_counter = FpsCounter()

        try:
            camera = create_camera(
                self.cfg.camera_width,
                self.cfg.camera_height,
                self.cfg.camera_fps,
            )
            logger.info("camera initialized backend=%s", camera.backend)

            while not self._stop.is_set():
                frame = camera.read()
                if frame is None:
                    time.sleep(0.01)
                    continue

                frame_index += 1
                capture_fps = capture_fps_counter.tick()

                if frame_index % self.cfg.process_every_n_frames != 0:
                    if self.debug_window:
                        self._show_debug(frame, None)
                    continue

                if not self._inference or not self._inference.is_loaded:
                    continue

                result = self._inference.predict(frame)
                processed_count += 1
                process_fps = process_fps_counter.tick()

                infer_ms = result.get("inference_ms", 0)
                detections = result.get("detections", [])
                in_cooldown = self._in_cooldown()
                cooldown_left = 0.0
                if in_cooldown and self._last_alert_time > 0:
                    cooldown_left = max(
                        0, self.cfg.detection_cooldown - (time.time() - self._last_alert_time)
                    )

                log_performance(
                    frame_index=frame_index,
                    processed_count=processed_count,
                    inference_ms=infer_ms,
                    capture_fps=capture_fps,
                    processed_fps=process_fps,
                )
                if detections:
                    logger.info(
                        "Detections | %s | cooldown=%s (%.0fs left)",
                        ", ".join(
                            f"{d['label']} {d['confidence']:.2f}" for d in detections
                        ),
                        "active" if in_cooldown else "ready",
                        cooldown_left,
                    )

                confirmed = temporal.update(
                    result["fire_detected"],
                    result["smoke_detected"],
                )

                # Same-frame fire+smoke: confirm immediately (common on Pi)
                if (
                    self.cfg.instant_dual_confirm
                    and result["fire_detected"]
                    and result["smoke_detected"]
                    and result.get("fire_confidence", 0) >= self.cfg.fire_threshold
                    and result.get("smoke_confidence", 0) >= self.cfg.smoke_threshold
                ):
                    confirmed["both_confirmed"] = True

                if detections and not any(
                    (
                        confirmed["both_confirmed"],
                        confirmed["fire_confirmed"],
                        confirmed["smoke_confirmed"],
                    )
                ):
                    logger.debug(
                        "confirmation pending | fire %s/%s smoke %s/%s both %s/%s",
                        confirmed["fire_hits"],
                        self.cfg.fire_required,
                        confirmed["smoke_hits"],
                        self.cfg.smoke_required,
                        confirmed["both_hits"],
                        self.cfg.both_required,
                    )

                if self.debug_window:
                    self._show_debug(frame, result)

                if self._in_cooldown():
                    continue

                event_type = None
                if confirmed["both_confirmed"]:
                    event_type = "fire_smoke"
                elif confirmed["fire_confirmed"]:
                    event_type = "fire"
                elif confirmed["smoke_confirmed"]:
                    event_type = "smoke"

                if not event_type:
                    continue

                logger.warning(
                    "detection confirmed | type=%s fire=%.2f smoke=%.2f — sending alert",
                    event_type,
                    result.get("fire_confidence", 0),
                    result.get("smoke_confidence", 0),
                )
                self._handle_alert(frame, result, event_type)
                temporal.reset()

        except Exception as exc:
            logger.exception("Detection loop error: %s", exc)
        finally:
            if camera:
                camera.stop()
            if self.debug_window:
                try:
                    import cv2

                    cv2.destroyAllWindows()
                except Exception:
                    pass
            logger.info("Detection loop stopped")

    def _show_debug(self, frame, result) -> None:
        try:
            import cv2

            from detector.utils import draw_boxes

            if result and result.get("detections"):
                display = draw_boxes(frame, result["detections"])
            else:
                display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow("NaarFind Detection", display)
            cv2.waitKey(1)
        except Exception:
            pass

    def _handle_alert(self, frame, result: dict, event_type: str) -> None:
        fire_conf = result.get("fire_confidence", 0.0)
        smoke_conf = result.get("smoke_confidence", 0.0)
        detections = result.get("detections", [])
        timestamp = datetime.now(timezone.utc).isoformat()

        local_path = None
        if self.cfg.save_snapshots:
            try:
                local_path = save_snapshot(
                    frame,
                    detections,
                    self.cfg.snapshot_dir,
                    prefix=event_type,
                )
                logger.info("snapshot saved path=%s", local_path)
            except Exception as exc:
                logger.error("snapshot save failed: %s", exc)

        payload = {
            "event_type": event_type,
            "risk_level": _risk_level(fire_conf, smoke_conf, event_type),
            "fire_confidence": fire_conf,
            "smoke_confidence": smoke_conf,
            "confidence": max(fire_conf, smoke_conf),
            "detections": detections,
            "local_image_path": str(local_path) if local_path else None,
            "timestamp": timestamp,
            "frame_rgb": frame,
            "local_path": local_path,
        }

        logger.warning(
            "ALERT %s fire=%.2f smoke=%.2f risk=%s",
            event_type,
            fire_conf,
            smoke_conf,
            payload["risk_level"],
        )

        self._last_alert_time = time.time()
        try:
            self.on_alert(payload)
        except Exception as exc:
            logger.error("Alert handler failed: %s", exc)
