"""YOLO fire/smoke inference — NCNN (Pi) or .pt fallback."""

import logging
import time
from pathlib import Path

import numpy as np

from detector.config import config

logger = logging.getLogger(__name__)

EMPTY_RESULT = {
    "fire_detected": False,
    "smoke_detected": False,
    "fire_confidence": 0.0,
    "smoke_confidence": 0.0,
    "detections": [],
}


class YOLOFireSmokeInference:
    """Ultralytics YOLO — NCNN folder preferred, .pt fallback."""

    def __init__(
        self,
        model_path: Path | None = None,
        fallback_path: Path | None = None,
        img_size: int | None = None,
        fire_threshold: float | None = None,
        smoke_threshold: float | None = None,
    ) -> None:
        self.model_path = model_path or config.model_path
        self.fallback_path = fallback_path or config.model_fallback_path
        self.img_size = img_size or config.model_img_size
        self.fire_threshold = fire_threshold or config.fire_threshold
        self.smoke_threshold = smoke_threshold or config.smoke_threshold
        self._model = None
        self._loaded_path: Path | None = None
        self._class_names: dict[int, str] = {}

    def _resolve_model_file(self) -> Path | None:
        for path in (self.model_path, self.fallback_path):
            if not path.exists():
                continue
            if path.is_file() and path.suffix == ".pt":
                return path
            if path.is_dir():
                if path.name.endswith("_ncnn_model") or (path / "metadata.yaml").is_file():
                    return path
                if any(path.iterdir()):
                    return path
        return None

    def load_model(self) -> bool:
        resolved = self._resolve_model_file()
        if not resolved:
            logger.warning(
                "No YOLO model found. Checked:\n  %s\n  %s\n"
                "Detection disabled — heartbeat will continue.",
                self.model_path,
                self.fallback_path,
            )
            return False

        try:
            from ultralytics import YOLO

            logger.info("Loading YOLO model from %s (imgsz=%s)", resolved, self.img_size)
            self._model = YOLO(str(resolved))
            self._loaded_path = resolved
            names = getattr(self._model, "names", {}) or {}
            self._class_names = {int(k): str(v).lower() for k, v in names.items()}
            if not self._class_names:
                self._class_names = {0: "fire", 1: "smoke"}
            logger.info("Model loaded. Classes: %s", self._class_names)
            return True
        except Exception as exc:
            logger.error("Failed to load YOLO model: %s", exc)
            self._model = None
            return False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _label_for_class(self, class_id: int) -> str:
        name = self._class_names.get(class_id, "").lower()
        if "fire" in name:
            return "fire"
        if "smoke" in name:
            return "smoke"
        if class_id == 0:
            return "fire"
        if class_id == 1:
            return "smoke"
        return name or f"class_{class_id}"

    def predict(self, frame: np.ndarray) -> dict:
        if not self.is_loaded or frame is None:
            return dict(EMPTY_RESULT)

        start = time.perf_counter()
        try:
            results = self._model.predict(
                frame,
                imgsz=self.img_size,
                verbose=False,
                conf=min(self.fire_threshold, self.smoke_threshold) * 0.5,
            )
        except Exception as exc:
            logger.error("Inference error: %s", exc)
            return dict(EMPTY_RESULT)

        elapsed_ms = (time.perf_counter() - start) * 1000
        detections: list[dict] = []
        fire_conf = 0.0
        smoke_conf = 0.0

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = self._label_for_class(class_id)
                xyxy = box.xyxy[0].tolist()
                bbox = [int(v) for v in xyxy]

                if label == "fire" and conf >= self.fire_threshold:
                    fire_conf = max(fire_conf, conf)
                    detections.append(
                        {"label": "fire", "confidence": conf, "bbox": bbox}
                    )
                elif label == "smoke" and conf >= self.smoke_threshold:
                    smoke_conf = max(smoke_conf, conf)
                    detections.append(
                        {"label": "smoke", "confidence": conf, "bbox": bbox}
                    )

        out = {
            "fire_detected": fire_conf >= self.fire_threshold,
            "smoke_detected": smoke_conf >= self.smoke_threshold,
            "fire_confidence": round(fire_conf, 4),
            "smoke_confidence": round(smoke_conf, 4),
            "detections": detections,
            "inference_ms": round(elapsed_ms, 1),
        }
        return out
