"""Explicit JSON export with input protection and atomic publication."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from trueme.errors import ReportError

INTERPRETATION = (
    "This score compares photos under the selected model. "
    "It does not predict acceptance by third-party identity verification systems."
)


def build_report(
    reference: Path,
    probe: Path,
    comparison: dict,
    models: list[dict],
    device: dict,
    app_version: str,
) -> dict:
    return {
        "schema_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "application_version": app_version,
        "models": models,
        "device": device,
        "inputs": {"reference": reference.name, "probe": probe.name},
        "cosine_similarity": comparison["cosine_similarity"],
        "quality_warnings": comparison["quality_warnings"],
        "interpretation": INTERPRETATION,
    }


def _check_destination(destination: Path, inputs: tuple[Path, Path], overwrite: bool) -> None:
    if destination.is_symlink():
        raise ReportError("Report destination must not be a symbolic link.")
    for source in inputs:
        if destination.resolve() == source.resolve() or (
            destination.exists() and source.exists() and destination.samefile(source)
        ):
            raise ReportError(
                "Report destination must not overwrite an input image or its aliases."
            )
    if destination.exists() and not overwrite:
        raise ReportError("Report already exists; use --overwrite to replace it.")
    if destination.exists() and not destination.is_file():
        raise ReportError("Report destination must be a regular file.")


def write_report(
    report: dict,
    destination: Path,
    inputs: tuple[Path, Path],
    overwrite: bool = False,
) -> None:
    temporary = None
    try:
        _check_destination(destination, inputs, overwrite)
        content = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, prefix=".trueme-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        _check_destination(destination, inputs, overwrite)
        if overwrite:
            os.replace(temporary, destination)
        else:
            # Linking publishes the complete report without replacing a concurrently created file.
            os.link(temporary, destination)
    except (OSError, ValueError) as exc:
        raise ReportError(
            "Cannot write report; check its destination, permissions, and finite JSON values."
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
