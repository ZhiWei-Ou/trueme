"""OS-specific per-user storage conventions."""

import os
import sys
from pathlib import Path

from .base import PlatformPaths


class LinuxPaths(PlatformPaths):
    def model_dir(self) -> Path:
        configured = os.environ.get("XDG_DATA_HOME", "")
        base = Path(configured) if configured and Path(configured).is_absolute() else (
            Path.home() / ".local" / "share"
        )
        return base / "trueme" / "models"


class MacOSPaths(PlatformPaths):
    def model_dir(self) -> Path:
        return Path.home() / "Library" / "Application Support" / "TrueMe" / "models"


class WindowsPaths(PlatformPaths):
    def model_dir(self) -> Path:
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "TrueMe" / "models"


def select_platform() -> PlatformPaths:
    if sys.platform == "win32":
        return WindowsPaths()
    if sys.platform == "darwin":
        return MacOSPaths()
    if sys.platform.startswith("linux"):
        return LinuxPaths()
    raise RuntimeError(f"Unsupported platform: {sys.platform}")
