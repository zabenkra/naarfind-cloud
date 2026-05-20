"""YOLO fire/smoke model loading and single-frame inference."""

import logging
from pathlib import Path

import numpy as np

from ai.camera import CAMERA_TEST_PATH, capture_frame
from detector.config import config
from detector.inference import YOLOFireSmokeInference

logger = logging.getLogger(__name__)


class FireSmokeDetector:
    """Thin wrapper around YOLO inference for the ai runtime."""

    def __init__(self) -> None:
        self._engine = YOLOFireSmokeInference()
        self._loaded = False

    @property
    def model_path(self) -> Path | None:
        return self._engine._loaded_path

    @property
    def classes(self) -> dict[int, str]:
        return dict(self._engine._class_names)

    def load(self) -> bool:
        self._loaded = self._engine.load_model()
        return self._loaded

    def predict(self, frame: np.ndarray) -> dict:
        return self._engine.predict(frame)


def _load_test_frame() -> np.ndarray | None:
    if CAMERA_TEST_PATH.is_file():
        import cv2

        bgr = cv2.imread(str(CAMERA_TEST_PATH))
        if bgr is not None:
            logger.info("Using test frame from %s", CAMERA_TEST_PATH)
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    frame, _ = capture_frame()
    return frame


def run_ai_test() -> int:
    """
    Load model from MODEL_PATH, run one inference, print model info and detections.
    """
    print("Loading AI model...")
    detector = FireSmokeDetector()

    if not detector.load():
        print("FAIL: Model not loaded")
        print(f"  MODEL_PATH={config.model_path}")
        print(f"  MODEL_FALLBACK_PATH={config.model_fallback_path}")
        return 1

    print("model loaded")
    print(f"model path: {detector.model_path}")
    print(f"classes: {detector.classes}")

    frame = _load_test_frame()
    if frame is None:
        print("FAIL: No test frame (run --camera-test first or connect camera)")
        return 1

    print("Running inference...")
    result = detector.predict(frame)

    infer_ms = result.get("inference_ms", 0)
    print(f"inference time: {infer_ms}ms")
    print(f"fire_detected: {result.get('fire_detected')}")
    print(f"smoke_detected: {result.get('smoke_detected')}")
    print(f"fire_confidence: {result.get('fire_confidence')}")
    print(f"smoke_confidence: {result.get('smoke_confidence')}")

    detections = result.get("detections", [])
    if detections:
        print("detections:")
        for det in detections:
            print(
                f"  - {det['label']} conf={det['confidence']:.2f} bbox={det['bbox']}"
            )
    else:
        print("detections: (none above threshold)")

    print("SUCCESS: AI test complete")
    return 0
