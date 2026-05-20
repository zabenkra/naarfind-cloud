"""Camera capture for AI runtime."""

import logging
from pathlib import Path

import cv2
import numpy as np

from detector.camera import create_camera
from detector.config import config

logger = logging.getLogger(__name__)

_EDGE_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = _EDGE_ROOT / "captures"
CAMERA_TEST_PATH = CAPTURE_DIR / "camera_test.jpg"


def capture_frame() -> tuple[np.ndarray | None, str]:
    """Open camera, read one frame, return (frame, backend_name)."""
    camera = None
    try:
        camera = create_camera(config.camera_width, config.camera_height, config.camera_fps)
        logger.info("Camera initialized backend=%s", camera.backend)
        frame = camera.read()
        return frame, camera.backend
    finally:
        if camera:
            camera.stop()


def save_frame_bgr(frame_rgb: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr)
    return path


def run_camera_test() -> int:
    """
    Initialize CSI/OpenCV camera, capture one frame, save captures/camera_test.jpg.
    """
    print("Initializing camera...")
    try:
        frame, backend = capture_frame()
        if frame is None:
            print("FAIL: No frame captured")
            return 1

        path = save_frame_bgr(frame, CAMERA_TEST_PATH)
        print("SUCCESS: Camera test passed")
        print(f"  backend={backend}")
        print(f"  resolution={frame.shape[1]}x{frame.shape[0]}")
        print(f"  saved={path}")
        logger.info("Camera test saved %s", path)
        return 0
    except Exception as exc:
        print(f"FAIL: Camera test failed — {exc}")
        logger.exception("Camera test error")
        return 1
