"""Weight-independent diagnostics plus explicit session initialization results."""

import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from trueme import __version__
from trueme.errors import TrueMeError


def diagnose(model_dir: Path) -> dict:
    from trueme.models.registry import inspect_models

    result = {
        "application_version": __version__,
        "python": sys.version.split()[0],
        "os": platform.platform(),
        "model_directory": str(model_dir),
        "models": inspect_models(model_dir),
        "available_providers": [],
        "session_initialization": {},
        "inference": "not run; use compare with consented photos",
    }
    try:
        result["onnxruntime_version"] = version("onnxruntime")
    except PackageNotFoundError:
        try:
            result["onnxruntime_version"] = version("onnxruntime-gpu")
        except PackageNotFoundError:
            result["onnxruntime_version"] = None
    try:
        import onnxruntime as ort
    except (ImportError, OSError):
        result["guidance"] = (
            "Install the CPU or GPU environment with make setup; see docs/installation.md."
        )
        return result
    result["available_providers"] = ort.get_available_providers()
    from trueme.models import create_models

    for device in ("cpu", "cuda"):
        try:
            bundle = create_models(model_dir, device)
            result["session_initialization"][device] = {
                "ok": True,
                "device": bundle.device_info(),
            }
        except TrueMeError as exc:
            result["session_initialization"][device] = {"ok": False, "reason": str(exc)}
    result["guidance"] = (
        "Initialization does not establish successful inference. GPU needs a compatible "
        "ONNX Runtime GPU / CUDA / cuDNN installation; see docs/installation.md."
    )
    return result
