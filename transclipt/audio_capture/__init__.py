"""Audio capture using ScreenCaptureKit via Swift CLI helper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_BINARY_PATH = Path(__file__).parent / "audio_capture"
_BUILD_SCRIPT = Path(__file__).parent / "build.sh"


def is_available() -> bool:
    if sys.platform != "darwin":
        return False
    if not _BINARY_PATH.exists():
        return _try_build()
    return True


def _try_build() -> bool:
    if not _BUILD_SCRIPT.exists():
        return False
    try:
        result = subprocess.run(
            ["bash", str(_BUILD_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0 and _BINARY_PATH.exists()
    except (subprocess.TimeoutExpired, OSError):
        return False


def capture_audio(
    output_path: Path,
    duration: float,
    pid: int | None = None,
) -> bool:
    if not is_available():
        return False

    cmd = [str(_BINARY_PATH), str(output_path), str(duration)]
    if pid is not None:
        cmd.append(str(pid))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 30,
        )
        return result.returncode == 0 and output_path.exists()
    except (subprocess.TimeoutExpired, OSError):
        return False
