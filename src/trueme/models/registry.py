"""Packaged, pinned model metadata; no network access."""

import hashlib
import json
from importlib.resources import files
from pathlib import Path

from trueme.errors import ModelError


def load_manifest() -> list[dict]:
    return json.loads(files("trueme.models").joinpath("manifest.json").read_text("utf-8"))


def inspect_models(model_dir: Path) -> list[dict]:
    return [
        dict(model, present=(model_dir / model["filename"]).is_file()) for model in load_manifest()
    ]


def validated_models(model_dir: Path) -> list[dict]:
    models = load_manifest()
    for model in models:
        path = model_dir / model["filename"]
        try:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
        except OSError as exc:
            raise ModelError(
                f"Cannot read {model['filename']}. Acquire the models described in docs/models.md "
                "and set --model-dir or TRUEME_MODEL_DIR."
            ) from exc
        if digest != model["sha256"]:
            raise ModelError(
                f"Checksum mismatch for {model['filename']}; download the pinned official weight."
            )
    return models
