"""Camera capture: Raspberry Pi CSI (picamera2) or OpenCV fallback."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class CameraBase(ABC):
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def read(self) -> np.ndarray | None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @property
    @abstractmethod
    def backend(self) -> str: ...


class CSICamera(CameraBase):
    """Raspberry Pi CSI camera via picamera2."""

    def __init__(self, width: int, height: int, fps: int) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self._picam = None

    @property
    def backend(self) -> str:
        return "picamera2"

    def start(self) -> None:
        from picamera2 import Picamera2

        self._picam = Picamera2()
        config = self._picam.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"},
        )
        self._picam.configure(config)
        self._picam.start()
        time.sleep(1.0)
        logger.info("CSI camera started %dx%d @ ~%dfps", self.width, self.height, self.fps)

    def read(self) -> np.ndarray | None:
        if not self._picam:
            return None
        frame = self._picam.capture_array()
        if frame is None:
            return None
        # picamera2 returns RGB; OpenCV uses BGR elsewhere — keep RGB for YOLO
        return frame

    def stop(self) -> None:
        if self._picam:
            self._picam.stop()
            self._picam.close()
            self._picam = None
            logger.info("CSI camera stopped")


class OpenCVCamera(CameraBase):
    """USB / laptop webcam fallback."""

    def __init__(self, width: int, height: int, fps: int, device_index: int = 0) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.device_index = device_index
        self._cap = None

    @property
    def backend(self) -> str:
        return "opencv"

    def start(self) -> None:
        import cv2

        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"OpenCV could not open camera index {self.device_index}")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        logger.info(
            "OpenCV camera started index=%s %dx%d",
            self.device_index,
            self.width,
            self.height,
        )

    def read(self) -> np.ndarray | None:
        if not self._cap:
            return None
        import cv2

        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def stop(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
            logger.info("OpenCV camera stopped")


def run_camera_test(output_path: Path | None = None) -> int:
    """
    Open CSI (picamera2) or OpenCV camera, capture one frame, save JPEG.
    Default: snapshots/camera_test.jpg
    """
    from detector.config import config

    out = output_path or (config.snapshot_dir / "camera_test.jpg")
    out.parent.mkdir(parents=True, exist_ok=True)

    print("Opening camera...")
    camera = None
    try:
        camera = create_camera(config.camera_width, config.camera_height, config.camera_fps)
        frame = camera.read()
        if frame is None:
            print("FAIL: No frame captured")
            return 1

        import cv2

        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(out), bgr)

        print("SUCCESS: Camera test passed")
        print(f"  backend={camera.backend}")
        print(f"  resolution={frame.shape[1]}x{frame.shape[0]}")
        print(f"  saved={out.resolve()}")
        logger.info("Camera test saved %s", out)
        return 0
    except Exception as exc:
        print(f"FAIL: Camera test failed — {exc}")
        logger.exception("Camera test error")
        return 1
    finally:
        if camera:
            camera.stop()


def create_camera(width: int, height: int, fps: int, prefer_csi: bool = True) -> CameraBase:
    """Try picamera2 on Pi, fall back to OpenCV."""
    if prefer_csi:
        try:
            camera = CSICamera(width, height, fps)
            camera.start()
            frame = camera.read()
            if frame is not None:
                return camera
            camera.stop()
            logger.warning("CSI camera returned no frame; trying OpenCV")
        except Exception as exc:
            logger.warning("picamera2 unavailable (%s); using OpenCV fallback", exc)

    camera = OpenCVCamera(width, height, fps)
    camera.start()
    return camera
