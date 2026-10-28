"""Construct the two pinned adapters without initializing models at import."""

from pathlib import Path

from .registry import validated_models


class ModelBundle:
    def __init__(self, model_dir: Path, device: str):
        from .device import ModelSession
        from .onnx import SFace, YuNet

        self._models = validated_models(model_dir)
        self.requested = device
        self._sessions = {
            model["role"]: ModelSession(model_dir / model["filename"], device)
            for model in self._models
        }
        self.detector = YuNet(self._sessions["detector"])
        self.recognizer = SFace(self._sessions["recognizer"])

    def metadata(self) -> list[dict]:
        return [
            {key: model[key] for key in ("name", "version", "sha256")} for model in self._models
        ]

    def device_info(self) -> dict:
        return {
            "requested": self.requested,
            "sessions": {role: session.info() for role, session in self._sessions.items()},
            "note": "Configured providers do not prove every operation ran on GPU.",
        }


def create_models(model_dir: Path, device: str = "auto") -> ModelBundle:
    return ModelBundle(model_dir, device)
