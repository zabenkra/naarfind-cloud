#!/usr/bin/env python3
"""Generate alert.wav and a minimal alert.mp3 for the dashboard."""

import math
import struct
import wave
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"


def write_wav(path: Path) -> None:
    sample_rate = 44100
    duration = 0.4
    freq = 880
    n = int(sample_rate * duration)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        for i in range(n):
            t = i / sample_rate
            envelope = 1 - (t / duration)
            val = int(32767 * 0.35 * math.sin(2 * math.pi * freq * t) * envelope)
            w.writeframes(struct.pack("<h", val))


def write_minimal_mp3(path: Path) -> None:
    # Minimal valid MPEG audio frame (short beep-like frame sequence)
    path.write_bytes(
        bytes.fromhex(
            "fff348c400000000000027800000000f00000069736f6d000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "fff348c400000000000027800000000f00000069736f6d000000000000000000"
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            "ffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )
    )


if __name__ == "__main__":
    PUBLIC.mkdir(parents=True, exist_ok=True)
    write_wav(PUBLIC / "alert.wav")
    write_minimal_mp3(PUBLIC / "alert.mp3")
    print("Generated alert.wav and alert.mp3 in", PUBLIC)
