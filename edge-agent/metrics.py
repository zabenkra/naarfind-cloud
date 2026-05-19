"""Lightweight Pi system metrics (no extra dependencies)."""

import os
import shutil
from pathlib import Path


def read_cpu_temp_celsius() -> float | None:
    thermal = Path("/sys/class/thermal/thermal_zone0/temp")
    if not thermal.is_file():
        return None
    try:
        return round(int(thermal.read_text().strip()) / 1000.0, 1)
    except (OSError, ValueError):
        return None


def read_ram_usage_percent() -> float | None:
    try:
        with open("/proc/meminfo", encoding="utf-8") as handle:
            lines = {line.split(":")[0]: line for line in handle}
        total = int(lines["MemTotal"].split()[1])
        available = int(lines.get("MemAvailable", lines["MemFree"]).split()[1])
        used = total - available
        return round(used / total * 100, 1) if total else None
    except (OSError, KeyError, ValueError, IndexError):
        return None


def read_disk_usage_percent(path: str = "/") -> float | None:
    try:
        usage = shutil.disk_usage(path)
        return round(usage.used / usage.total * 100, 1) if usage.total else None
    except OSError:
        return None


def read_camera_status() -> str:
    video_devices = list(Path("/dev").glob("video*"))
    return "ok" if video_devices else "unavailable"


def collect_metrics() -> dict:
    return {
        "cpu_temp": read_cpu_temp_celsius(),
        "ram_usage": read_ram_usage_percent(),
        "disk_usage": read_disk_usage_percent(),
        "camera_status": read_camera_status(),
    }
