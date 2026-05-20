"""Fire/smoke detection for NaarFind edge-agent."""

from detector.camera import run_camera_test
from detector.fire_detector import FireDetectorLoop

__all__ = ["FireDetectorLoop", "run_camera_test"]
