"""Pairwise processing; intermediate images and features stay in memory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from trueme.core.images import load_image
from trueme.core.quality import quality_warnings
from trueme.core.similarity import cosine_similarity
from trueme.errors import InputError

if TYPE_CHECKING:
    from trueme.models.interfaces import Detector, Recognizer


def compare_images(
    reference: Path, probe: Path, detector: Detector, recognizer: Recognizer
) -> dict:
    features = []
    warnings = {}
    for role, path in (("reference", reference), ("probe", probe)):
        image = load_image(path)
        faces = detector.detect(image)
        if len(faces) != 1:
            raise InputError(
                f"The {role} image must contain exactly one face; detected {len(faces)}."
            )
        face = faces[0]
        warnings[role] = quality_warnings(image, face.bbox)
        features.append(recognizer.embed(image, face))
    return {
        "cosine_similarity": cosine_similarity(*features),
        "quality_warnings": warnings,
    }
