"""Detection configuration from environment."""

import os
from pathlib import Path

_EDGE_ROOT = Path(__file__).resolve().parents[1]


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _resolve_path(raw: str) -> Path:
    path = Path(raw.strip())
    if not path.is_absolute():
        path = _EDGE_ROOT / path
    return path


class DetectorConfig:
    model_path: Path = _resolve_path(
        os.getenv("MODEL_PATH", "./models/fire_smoke_yolov8n_ncnn_model")
    )
    model_fallback_path: Path = _resolve_path(
        os.getenv("MODEL_FALLBACK_PATH", "./models/fire_smoke_yolov8n.pt")
    )
    model_img_size: int = _env_int("MODEL_IMG_SIZE", 416)
    fire_threshold: float = _env_float("FIRE_THRESHOLD", 0.55)
    smoke_threshold: float = _env_float("SMOKE_THRESHOLD", 0.65)
    detection_cooldown: int = _env_int("DETECTION_COOLDOWN", 30)
    camera_width: int = _env_int("CAMERA_WIDTH", 1280)
    camera_height: int = _env_int("CAMERA_HEIGHT", 720)
    camera_fps: int = _env_int("CAMERA_FPS", 20)
    process_every_n_frames: int = _env_int("PROCESS_EVERY_N_FRAMES", 3)
    enable_debug_window: bool = _env_bool("ENABLE_DEBUG_WINDOW", False)
    save_snapshots: bool = _env_bool("SAVE_SNAPSHOTS", True)
    upload_snapshots: bool = _env_bool("UPLOAD_SNAPSHOTS", True)
    snapshot_dir: Path = _resolve_path(os.getenv("SNAPSHOT_DIR", "./snapshots"))

    # Temporal confirmation
    fire_required: int = 3
    fire_window: int = 5
    smoke_required: int = 4
    smoke_window: int = 6
    both_required: int = 2
    both_window: int = 4


config = DetectorConfig()
