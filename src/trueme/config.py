"""Resolve user configuration independently of model execution."""

import os
from pathlib import Path

from .platforms.base import PlatformPaths


def resolve_model_dir(explicit: Path | None, paths: PlatformPaths) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    configured = os.environ.get("TRUEME_MODEL_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return paths.model_dir().resolve()
